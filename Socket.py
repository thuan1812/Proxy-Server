import socket
import threading
import time
import datetime
import configparser
import os
import shutil

def readConfig(filename):
    config = configparser.ConfigParser()
    try:
        config.read(filename)
        cacheTime = int(config["ProxyConfig"]["cache_time"])
        whitelisting = [domain.strip() for domain in config["ProxyConfig"]["whitelisting"].split(",")]
        timeRange = [int(t) for t in config["ProxyConfig"]["time"].split("-")]
        return cacheTime, whitelisting, timeRange
    except Exception as Error:
        print(f"Không thể đọc file config: {Error}")
        return None, None, None

def parseData(inputData):
    splitData = inputData.split(b"\r\n\r\n", 1)
    lines = splitData[0].split(b"\r\n")
    if len(lines) < 1:
        return None, None, None
    method, url, _ = lines[0].split(b" ", 2)
    headers = {}
    for line in lines[1:]:
        if b":" in line:
            key, value = line.split(b":", 1)
            key = key.strip().lower().decode("utf-8")
            value = value.strip().lower().decode("utf-8")
            headers[key] = value
    return [method.decode("utf-8"), url.decode("utf-8"), headers]

def error403(filename):
    try:
        with open(filename, "rb") as f:
            data = b"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n"
            data += f.read()
        return data
    except Exception as Error:
        print(f"Không đọc được file HTML: {Error}")
        return b"HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nError reading HTML file"

def isWhitelist(domain, whitelist):
    for allowedDomain in whitelist:
        if allowedDomain in domain:
            return True
    return False

def isInTimeZone(timeRange):
    now = datetime.datetime.now().time()
    start_time = datetime.time(timeRange[0])
    end_time = datetime.time(timeRange[1])
    return start_time <= now <= end_time

def getIpByDomainName(domainName):
    try:
        return socket.gethostbyname(domainName)
    except socket.gaierror:
        return None

def imageCache(cacheTimeout, cacheDirectory):
    if not os.path.exists(cacheDirectory):
        os.makedirs(cacheDirectory)
    
    def clearCache():
        while True:
            if time.time() - os.path.getctime(cacheDirectory) >= cacheTimeout:
                try:
                    shutil.rmtree(cacheDirectory)
                    os.makedirs(cacheDirectory)
                    print("Bộ nhớ đệm đã được xóa")
                except Exception as Error:
                    print(f"Không xóa được dữ liệu bộ nhớ đệm: {Error}")
            time.sleep(cacheTimeout)

    def get(website, imageName):
        filename = os.path.join(cacheDirectory, website, imageName)
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                return f.read()
        else:
            return None

    def put(website, imageName, imageData):
        websiteDirectory = os.path.join(cacheDirectory, website)
        if not os.path.exists(websiteDirectory):
            os.makedirs(websiteDirectory)
        filename = os.path.join(websiteDirectory, imageName)
        with open(filename, "wb") as f:
            f.write(imageData)
    
    cacheCleanupThread = threading.Thread(target=clearCache)
    cacheCleanupThread.daemon = True
    cacheCleanupThread.start()
    return get, put

def handleClient(clientSocket, clientAddress, whitelisting, timeRange, getImage, putImage):
    print(f"Kết nối mới: {clientAddress}")
    validMethods = ("GET", "HEAD", "POST")
    BUFFERSIZE = 6149

    try:
        clientDataSent = b""
        while b"\r\n\r\n" not in clientDataSent:
            data = clientSocket.recv(BUFFERSIZE)
            clientDataSent += data

        if len(clientDataSent) > 0:
            clientData = parseData(clientDataSent)

            if clientData[0] == None or clientData[0].upper() not in validMethods or not isWhitelist(clientData[1], whitelisting) or not isInTimeZone(timeRange):
                clientSocket.sendall(error403("data1.html"))
                return

            domainName = clientData[1].split("//")[-1].split("/")[0]
            filename = clientData[1].split("/")[-1]
            if "image/" in clientData[2].get("accept", "") and len(filename) > 0:
                cacheImage = getImage(domainName, filename)
                if cacheImage != None:
                    print("Dữ liệu đã được tải lên từ bộ nhớ đệm")
                    clientSocket.sendall(cacheImage)
                    return

            try:
                serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                serverAddress = (getIpByDomainName(domainName), 80)
                serverSocket.connect(serverAddress)
                print(f"Đã kết nối với: {domainName}")
                serverSocket.sendall(clientDataSent)

                serverDataSent = b""
                while b"\r\n\r\n" not in serverDataSent:
                    data = serverSocket.recv(BUFFERSIZE)
                    serverDataSent += data

                serverData = parseData(serverDataSent)

                if "transfer-encoding" in serverData[2]:
                    while not serverDataSent.endswith(b"0\r\n\r\n"):
                        try:
                            data = serverSocket.recv(BUFFERSIZE)
                            serverDataSent += data
                        except Exception as Error:
                            print(f"Không lấy được dữ liệu từ Server: {Error}")
                            break

                elif "content-length" in serverData[2]:
                    while len(serverDataSent[serverDataSent.find(b"\r\n\r\n") + len(b"\r\n\r\n") :]) < int(serverData[2].get("content-length", 0)):
                        try:
                            data = serverSocket.recv(BUFFERSIZE)
                            serverDataSent += data
                        except Exception as Error:
                            print(f"Không lấy dữ liệu từ Server: {Error}")
                            break

                if serverData[2].get("content-type", "").startswith("image/"):
                    putImage(domainName, filename, serverDataSent)

                clientSocket.sendall(serverDataSent)
            except Exception as Error:
                print(f"Không thể lấy IP từ {domainName}: {Error}")
            finally:
                serverSocket.close()

    except Exception as Error:
        print(f"Xảy ra lỗi với client socket: {Error}")
    finally:
        print(f"Đóng kết nối: {clientAddress}")
        clientSocket.close()

def main():
    cacheTimeout, whitelisting, timeRange = readConfig("config.ini")
    
    if cacheTimeout == None or cacheTimeout < 0:
        print("Không hợp lệ")
        return 
    
    if whitelisting == None:
        print("Không có tên miền")
        return
    
    if timeRange == None or timeRange[1] < timeRange[0] or timeRange[1] < 0 or timeRange[0] < 0:
        print("Thời gian hoạt động không hợp lệ")
        return

    listenAddress = ("127.0.0.1", 6000)
    backlog = 5
    cacheDirectory = "cache"
    getImage, putImage = imageCache(cacheTimeout, cacheDirectory)

    if cacheTimeout != None and whitelisting != None and timeRange != None:
        try:
            proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy.bind(listenAddress)
            proxy.listen(backlog)
            print(f"Proxy đang kết nối tại: {listenAddress}")

            while True:
                try:
                    clientSocket, clientAddress = proxy.accept()
                    clientThread = threading.Thread(target=handleClient, args=(clientSocket, clientAddress, whitelisting, timeRange, getImage, putImage))
                    clientThread.start()
                except Exception as Error:
                    print(f"Không thể kết nối: {Error}")
        except Exception as Error:
            print(f"Không thể cài đặt socket: {Error}")
        finally:
            proxy.close()

if __name__ == "__main__":
    main()
