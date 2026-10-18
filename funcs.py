def SelectionSort(array, start, end, column_index=0, reverse=False):
    for i in range(start, end):
        key = i
        for j in range(i + 1, end):
            a = array[j][column_index]
            b = array[key][column_index]
            if (a < b and not reverse) or (a > b and reverse):
                key = j
        array[i], array[key] = array[key], array[i]

        

def BubbleSort(array, start, end, column_index=0, reverse=False):
    for i in range(end - 1):
        swapped = False
        for j in range(end - i - 1):
            a = array[j][column_index]
            b = array[j + 1][column_index]
            if (a > b and not reverse) or (a < b and reverse):
                array[j], array[j + 1] = array[j + 1], array[j]
                swapped = True
        if not swapped:
            break
        
def InsertionSort(array, start, end, column_index=0, reverse=False):
    for x in range(start + 1, end):
        key_row = array[x]
        key_val = key_row[column_index]
        y = x - 1
        while y >= start:
            cmp_val = array[y][column_index]
            if (key_val < cmp_val and not reverse) or (key_val > cmp_val and reverse):
                array[y + 1] = array[y]
                y -= 1
            else:
                break
        array[y + 1] = key_row
        
        
def Merge(array, p, q, r, column_index=0, reverse=False):
    n1 = q - p + 1
    n2 = r - q

    # create temp arrays
    L = [array[p + i] for i in range(n1)]
    R = [array[q + 1 + j] for j in range(n2)]

    i = 0
    j = 0
    k = p

    while i < n1 and j < n2:
        # Extract comparison values
        left_val = L[i][column_index]
        right_val = R[j][column_index]

        # Comparison logic
        if (left_val <= right_val and not reverse) or (left_val > right_val and reverse):
            array[k] = L[i]
            i += 1
        else:
            array[k] = R[j]
            j += 1
        k += 1

    # Copy any remaining elements
    while i < n1:
        array[k] = L[i]
        i += 1
        k += 1

    while j < n2:
        array[k] = R[j]
        j += 1
        k += 1


def MergeSort(array, start, end, column_index=0, reverse=False):
    if start < end:
        mid = start + (end - start) // 2
        MergeSort(array, start, mid, column_index, reverse)
        MergeSort(array, mid + 1, end, column_index, reverse)
        Merge(array, start, mid, end, column_index, reverse)


def partition(array, low, high, column_index=0, reverse=False):
    pivot = array[high][column_index]
    i = low - 1

    for j in range(low, high):
        val = array[j][column_index]
        if (val <= pivot and not reverse) or (val >= pivot and reverse):
            i += 1
            array[i], array[j] = array[j], array[i]

    array[i + 1], array[high] = array[high], array[i + 1]
    return i + 1


def QuickSort(array, low, high, column_index=0, reverse=False):
    if low < high:
        pi = partition(array, low, high, column_index, reverse)
        QuickSort(array, low, pi - 1, column_index, reverse)
        QuickSort(array, pi + 1, high, column_index, reverse)


def counting_sort_for_radix(arr, exp, column_index=0):
    n = len(arr)
    output = [None] * n
    count = [0] * 10

    for i in range(n):
        num = int(float(arr[i][column_index]))
        index = (num // exp) % 10
        count[index] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    for i in range(n - 1, -1, -1):
        num = int(float(arr[i][column_index]))
        index = (num // exp) % 10
        count[index] -= 1
        output[count[index]] = arr[i]

    for i in range(n):
        arr[i] = output[i]


def RadixSort(array, column_index=0, reverse=False):
    nums = [int(float(row[column_index])) for row in array]
    max_val = max(nums)
    exp = 1
    while max_val // exp > 0:
        counting_sort_for_radix(array, exp, column_index)
        exp *= 10

    if reverse:
        array.reverse()


def BucketSort(array, column_index=0, reverse=False):
    if not array:
        return array

    nums = [float(row[column_index]) for row in array]
    max_val, min_val = max(nums), min(nums)
    size = len(nums)
    buckets = [[] for _ in range(size)]

    # Normalize numbers to 0–1
    for i, num in enumerate(nums):
        index = int(((num - min_val) / (max_val - min_val + 1e-9)) * (size - 1))
        buckets[index].append(array[i])

    sorted_arr = []
    for b in buckets:
        if b:
            b.sort(key=lambda x: float(x[column_index]))
            sorted_arr.extend(b)

    if reverse:
        sorted_arr.reverse()

    array[:] = sorted_arr


def CountingSort(array, column_index=0, reverse=False):
    # Convert values to integers
    nums = [int(float(row[column_index])) for row in array]

    max_val = max(nums)
    min_val = min(nums)
    k = max_val - min_val

    count = [0] * (k + 1)

    for n in nums:
        count[n - min_val] += 1

    for i in range(1, len(count)):
        count[i] += count[i - 1]

    output = [None] * len(nums)
    for i in range(len(nums) - 1, -1, -1):
        j = nums[i] - min_val
        count[j] -= 1
        output[count[j]] = array[i]

    if reverse:
        output.reverse()

    array[:] = output
