如何运行？
请先执行以下命令

1. pip install -r requirements.txt   (安装环境)
2. python manage.py makemigrations   (检查数据库)
3. python manage.py migrate          (迁移数据库)
4. python manage.py createsuperuser (设置超级管理员,**请不要使用管理员账户登录网站**)
5. python manage.py runserver      (运行django，默认8000)

默认调转到home页面，数据库用的是django自带的sqlite3 