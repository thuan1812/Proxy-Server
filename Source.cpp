#include <iostream>
#include <string>
#include <fstream>
#include <chrono>
#include <vector>
#include <algorithm>
using namespace std;

void quickSort(int* a, int left, int right) 
{
    int i = left, j = right;
    int pivot = a[(left + right) / 2];
    while (i <= j) 
    {
        while (a[i] < pivot) 
        {
            i++;
        }
        while (a[j] > pivot) 
        {
            j--;
        }
        if (i <= j) 
        {
            swap(a[i], a[j]);
            i++;
            j--;
        }
    }

    if (left < j) 
        quickSort(a, left, j);
    
    if (i < right) 
        quickSort(a, i, right);

}

// https://www.geeksforgeeks.org/introduction-to-block-sort/
/*void blockSort(int* arr, int size, int blockSize)
{
    for (int i = 0; i < size; i += blockSize)
    {
        int right = min(i + blockSize - 1, size - 1);
        quickSort(arr, i, right);
    }

    int* result = new int[size];
    int resultIndex = 0;

    while (resultIndex < size)
    {
        int minIdx = 0;
        for (int i = 1; i < size; i += blockSize)
        {
            if (arr[i] < arr[minIdx])
            {
                minIdx = i;
            }
        }
        if (arr[minIdx] == INT_MAX)
        {
            break;
        }
        result[resultIndex] = arr[minIdx];
        arr[minIdx] = INT_MAX; 
        resultIndex++;

        for (int i = 0; i < blockSize; i++)
        {
            if (arr[minIdx + i] == INT_MAX)
            {
                arr[minIdx + i] = INT_MAX;
            }
        }
    }

    delete[] result;
}*/

void blockSort(int arr[], int size, int blockSize) {
    int numBlocks = (size + blockSize - 1) / blockSize;

    for (int i = 0; i < numBlocks; i++) {
        int left = i * blockSize;
        int right = min((i + 1) * blockSize, size);

        quickSort(arr, left, right - 1);
    }

    int* result = new int[size];
    int* blockIndices = new int[numBlocks];
    for (int i = 0; i < numBlocks; i++) {
        blockIndices[i] = i * blockSize;
    }

    for (int i = 0; i < size; i++) {
        int minVal = arr[blockIndices[0]];
        int blockIndex = 0;

        for (int j = 1; j < numBlocks; j++) {
            if (blockIndices[j] < (j + 1) * blockSize && arr[blockIndices[j]] < minVal) {
                minVal = arr[blockIndices[j]];
                blockIndex = j;
            }
        }

        result[i] = minVal;
        blockIndices[blockIndex]++;
    }

    for (int i = 0; i < size; i++) {
        arr[i] = result[i];
    }

    delete[] result;
    delete[] blockIndices;
}

const int RUN = 32;

void insertionSort(int* arr, int n) 
{
    for (int i = 1; i < n; i++) 
    {
        int v = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > v) 
        {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = v;
    }
}

void merge(int* a, int left, int mid, int right) 
{
    int n1 = mid - left + 1;
    int n2 = right - mid;
    int* L = new int[n1];
    int* R = new int[n2];
    for (int i = 0; i < n1; i++)
        L[i] = a[left + i];
    for (int i = 0; i < n2; i++)
        R[i] = a[mid + 1 + i];
    int i = 0, j = 0, k = left;
    while (i < n1 && j < n2) 
    {
        if (L[i] <= R[j]) 
        {
            a[k] = L[i];
            i++;
        }
        else 
        {
            a[k] = R[j];
            j++;
        }
        k++;
    }
    while (i < n1) 
    {
        a[k] = L[i];
        i++;
        k++;
    }
    while (j < n2) 
    {
        a[k] = R[j];
        j++;
        k++;
    }
}

// https://www.geeksforgeeks.org/timsort/
void timSort(int* arr, int size) 
{   
    for (int i = 0; i < size; i += RUN) 
    {
        int j = i + RUN - 1;
        if (j >= size) {
            j = size - 1;
        }
        insertionSort(arr + i, j - i + 1);
    }

    for (int mergeSize = RUN; mergeSize < size; mergeSize *= 2)
    {
        for (int left = 0; left < size; left += 2 * mergeSize)
        {
            int mid = left + mergeSize - 1;
            int right = min(left + 2 * mergeSize - 1, size - 1);
            if (mid < right) 
                merge(arr, left, mid, right);
        }
    }
}

void printArray(int* arr, int n)
{
    for (int i = 0; i < n; i++)
        cout << arr[i] << " ";
    cout << endl;
}


int main() {
    ifstream* fi = new ifstream[4];
    ofstream* fo = new ofstream[4];

    int inputSize[] = { 10000, 100000, 1000000 };
    int blockSize = 1000000;

    for (int i = 0; i < 3; i++) 
    {
        cout << "Part " << i << "\n";
        int n = inputSize[i];
        string* s = new string[3];
        s[0] = "randomized_data_" + to_string(n);
        s[1] = "sorted_data_" + to_string(n);
        s[2] = "reversed_sorted_data_" + to_string(n);

        for (int j = 0; j < 3; j++) 
        {
            fi[j].open(s[j] + ".txt");
            fo[j].open(s[j] + "_result.txt");
        }

        int* a = new int[n];

        chrono::time_point<chrono::high_resolution_clock> start, end;

        for (int j = 0; j < 3; j++) 
        {
            for (int k = 0; k < n; k++) 
            {
                fi[j] >> a[k];
            }

            start = chrono::high_resolution_clock::now();
            blockSort(a, n, blockSize);
            end = chrono::high_resolution_clock::now();
            chrono::duration<double> elapsed_seconds = end - start;
            cout << "Time used for " << j << ": " << elapsed_seconds.count() * 1000 << "\n";

            for (int k = 0; k < n; k++) 
            {
                fo[j] << a[k] << " ";
            }

            fi[j].clear();
            fi[j].seekg(0, ios::beg);
            for (int k = 0; k < n; k++) 
            {
                fi[j] >> a[k];
            }
        }
        delete[] a;

        for (int j = 0; j < 4; j++) 
        {
            fi[j].close();
            fo[j].close();
        }
        delete[] s;

    }

    delete[] fi;
    delete[] fo;
    return 0;
}
