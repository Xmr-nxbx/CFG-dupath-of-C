void Pi()
{
	double pi = 2,temp = 2;            //初始化pi值和临时值
	int numerator = 1,denominator = 3; //初始化分子和分母

	while(temp > 1e-16)                //数列大于指定精度
	{
		temp = temp*numerator/denominator;//计算一个数列的值
		pi += temp;
		numerator++;
		denominator += 2;
	}
	printf("PI = %.18f\n",pi);
}