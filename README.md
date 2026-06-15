# 粉糖QQ机器人

周周编写的QQ机器人，封装完整，可快速部署使用。<br />
该qqbot使用napcat+ncatbot实现程序操作QQ<br />
所有配置统一为 `/config.json`，只需创建python虚拟环境安装依赖，写好该配置文件即可完成程序部署。<br />
数据储存使用SQLite，无需额外准备环境且节约内存。<br />
AI大模型接口为deepseek，互联网搜索接口为博查。若更换接口则需要修改配置，并根据接口文档调整请求代码。<br />
`functions/test.py` 可见具体功能<br />
要编写新功能，在 functions/ 中创建文件，编写完毕后挂载到统一事件处理器 `functions/handers.py` 后重启生效。<br />
**完整见 docs/**<br />

参考项目：<br />
[白白的机叶](https://github.com/ReshiramXe/Graia_QQBOT_modules)<br />
[土豆的机仙](https://github.com/EvernightAurora/SylviBot)<br />
[暗风的猫猫bot](https://github.com/Jayfeather233/shinxbot2)<br>
