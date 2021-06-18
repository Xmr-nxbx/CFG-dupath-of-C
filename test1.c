void Array4_4()
{
	int A[4][4],B[4][4],i,j;
printf("%f\n",(3>2? A+2:1.0) );
	printf("Please Input 16 numbers:");
	for(i = 0; i < 4; i++)
		for(j = 0; j < 4; j++)
		{
			scanf("%d",&A[i][j]);  //输入16个数
			B[3-j][i] = A[i][j];   //旋转90度赋值
		}
	printf("Array A:\n");          //输出矩阵A
	for( i = 0; i < 4; i++)
	{
		for(j = 0 ; j < 4; j++)
		{
			printf("%4d",A[i][j]);
		}
		printf("\n");
	}
	printf("Array B:\n");          //输出矩阵B
	for( i = 0; i < 4; i++)
	{
		for(j = 0 ; j < 4; j++)
		{
			printf("%4d",B[i][j]);
		}
		printf("\n");
	}
}