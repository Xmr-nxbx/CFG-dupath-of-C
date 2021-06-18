#include <stdio.h>
#define MAXSIZE 10

// 递归的方式实现归并排序

// 实现归并，并把结果存放到list1
void merging(int *list1, int list1_size, int *list2, int list2_size)
{
    int i,j,k, m;
    int temp[MAXSIZE];

    i = j = k = 0;

    while(i < list1_size && j < list2_size)
    {
        if(list1[i] < list2[j])
        {
            temp[k] = list1[i];
            k++;
            i++;
        }
        else
        {
            temp[k++] = list2[j++];
        }
    }

    while(i < list1_size)
    {
        temp[k++] = list1[i++];
    }

    while(j < list2_size)
    {
        temp[k++] = list2[j++];
    }

    for(m = 0;m < (list1_size + list2_size);m++)
    {
        list1[m] = temp[m];
    }
}

void MergeSort(int k[], int n)
{
    if(n > 1)
    {
        /*
        *list1是左半部分，list2是右半部分
        */
        int *list1 = k;
        int list1_size = n/2;
        int *list2 = k + list1_size;
        int list2_size = n - list1_size;

        MergeSort(list1, list1_size);
        MergeSort(list2, list2_size);

        // 把两个合在一起
        merging(list1, list1_size, list2, list2_size);
    }

}

int main()
{
    int i, a[10] = {5, 2, 6, 0, 3, 9, 1, 7, 4, 8};

    MergeSort(a, 10);

    printf("answer:");

    for(i = 0;i < 10;i++)
    {
        printf("%d", a[i]);
    }
    printf("\n\n");

    return 0;
}