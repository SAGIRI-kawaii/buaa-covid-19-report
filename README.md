<h1 align="center" style="border-bottom: none">
  buaa-covid-19-report
</h1>

<p align="center">
  使用 Python 编写的自动填报北航 COVID-19 疫情信息的脚本。
</p>

## 使用方法
- 首先，确保你的 `Python` 版本大于等于 `3.8`
- 使用 `pip` 安装依赖，进入脚本所在文件夹，执行 `pip install -r requirements.txt`
- 进入 `config.json`，填写个人信息，支持多用户，各项含义请看下方 `配置文件`
- 运行脚本 `python main.py`，可配合 `crontab` 等方法实现每日定时打卡

## 配置文件
`config.json` 结构如下：
```json
{
  "users": [
    {
      "username": "",
      "password": "",
      "report_type": "",
      "notice_info": {
        "notice_type": "",
        "notice_key": ""
      }
    }
  ]
}
```
其中，各项含义如下
| 项 | 含义 | 备注 |
| ---- | ---- | ---- |
| username | 统一身份认证账号用户名 |  |
| password | 统一身份认证账号密码 |  |
| report_type | 填报类型 | 分为 `inner` ([buaaStudentNcov](https://app.buaa.edu.cn/site/buaaStudentNcov/index)) 和 `outer` ([ncov](https://app.buaa.edu.cn/ncov/wap/default/index))，请打卡前确认自己要打卡的页面并填入对应的名称 |
| notice_info | 打卡通知相关 | 若不需要通知可删除此项或保持原样 |
| notice_info -> notice_type | 通知使用应用 | 目前只支持 `ServerChan` 和 `bark` |
| notice_info -> notice_key | 通知应用Key | 其中 `ServerChan` 为 `SendKey`，`bark` 为 `https://api.day.app/{key}/{content}` 中 `key` 所在位置的值 |

## 多用户打卡
只需将用户信息填入 `config.json` 即可，示例如下：
```json
{
  "users": [
    {
      "username": "user1",
      "password": "pwd1",
      "report_type": "inner",
      "notice_info": {
        "notice_type": "bark",
        "notice_key": "bark_key"
      }
    },
    {
      "username": "user2",
      "password": "pwd2",
      "report_type": "outer",
      "notice_info": {
        "notice_type": "ServerChan",
        "notice_key": "SendKey"
      }
    }
  ]
}
```

## 免责声明

本程序以你所见到的样子呈现给你，不附带任何明示或暗示的担保，包括但不限于对功能合法性或对特定用途适用性的保证。在运行之前，你有责任理解其源代码的工作原理，并确认这是你想要执行的，本程序进行的操作都应被视为你本人进行、或由你授权代你进行的操作。在任何情况下，本程序作者与你决定运行本程序无关，不为你运行此程序所造成的任何损失、受到的处罚以及造成的法律后果等负任何责任。
