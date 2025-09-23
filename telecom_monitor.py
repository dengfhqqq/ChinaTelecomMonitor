#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Repo: https://github.com/Cp0204/ChinaTelecomMonitor
# ConfigFile: telecom_config.json
# Modify: 2025-09-23（多账号版）
#此版本是ai修改，只是为了方便查询多个号码而进行相应改版。

"""
任务名称
name: 电信套餐用量监控（多账号版）
定时规则
cron: 0 20 * * *
"""

import os
import sys
import json
import datetime
import calendar

# 兼容青龙
try:
    from telecom_class import Telecom
except:
    print("正在尝试自动安装依赖...")
    os.system("pip3 install pycryptodome requests &> /dev/null")
    from telecom_class import Telecom


CONFIG_DATA = {}
NOTIFYS = []
CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else "telecom_config.json"
TELECOM_FLUX_PACKAGE = os.environ.get("TELECOM_FLUX_PACKAGE", "true").lower() != "false"


# 发送通知消息
def send_notify(title, body):
    try:
        # 导入通知模块
        import notify

        # 如未配置 push_config 则使用青龙环境通知设置
        if CONFIG_DATA.get("push_config"):
            notify.push_config.update(CONFIG_DATA["push_config"])
            notify.push_config["CONSOLE"] = notify.push_config.get("CONSOLE", True)
        notify.send(title, body)
    except Exception as e:
        if e:
            print("发送通知消息失败！")


# 添加消息
def add_notify(text):
    global NOTIFYS
    NOTIFYS.append(text)
    print("📢", text)
    return text


def usage_status_icon(used, total):
    """流量使用状态图标"""
    if total <= 0:
        return "⚫"  # 无流量
    if used >= total:
        return "🔴"  # 超流量
    # 未超提示进度
    today = datetime.date.today()
    _, days_in_month = calendar.monthrange(today.year, today.month)
    time_progress = today.day / days_in_month
    usage_progress = used / total
    if usage_progress > time_progress * 1.5:
        return "🟠"  # 已超过均匀用量50%
    elif usage_progress > time_progress:
        return "🟡"  # 已超过均匀用量
    else:
        return "🟢"  # 均匀使用范围内


def process_account(phonenum, password):
    """处理单个账号的查询和通知"""
    # 为每个账号创建独立的Telecom实例
    telecom = Telecom()
    
    # 登录失败次数记录，按号码区分
    login_fail_key = f"loginFailTime_{phonenum}"
    login_fail_time = CONFIG_DATA.get(login_fail_key, 0)
    
    # 尝试登录
    if login_fail_time < 5:
        print(f"登录账号：{phonenum}")
        data = telecom.do_login(phonenum, password)
        if data.get("responseData", {}).get("resultCode") == "0000":
            print(f"登录成功：{phonenum}")
            login_info = data["responseData"]["data"]["loginSuccessResult"]
            login_info["phonenum"] = phonenum
            login_info["password"] = password  # 保存密码用于重新登录
            login_info["createTime"] = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            # 按号码保存登录信息
            CONFIG_DATA[f"login_info_{phonenum}"] = login_info
            CONFIG_DATA[login_fail_key] = 0
            telecom.set_login_info(login_info)
        else:
            login_fail_time += 1
            CONFIG_DATA[login_fail_key] = login_fail_time
            update_config()
            add_notify(f"登录失败：{phonenum}，已连续失败{login_fail_time}次")
            return False
    else:
        add_notify(f"登录受限：{phonenum}已连续失败{login_fail_time}次，为避免风控暂不执行")
        return False

    # 获取主要信息
    important_data = telecom.qry_important_data()
    if important_data.get("responseData"):
        print(f"获取信息成功：{phonenum}")
    elif important_data["headerInfos"]["code"] == "X201":
        print(f"信息获取失败，尝试重新登录：{phonenum}")
        # 重新登录
        data = telecom.do_login(phonenum, password)
        if data.get("responseData", {}).get("resultCode") == "0000":
            login_info = data["responseData"]["data"]["loginSuccessResult"]
            login_info["phonenum"] = phonenum
            login_info["password"] = password
            CONFIG_DATA[f"login_info_{phonenum}"] = login_info
            telecom.set_login_info(login_info)
            important_data = telecom.qry_important_data()
        else:
            add_notify(f"重新登录失败，无法获取信息：{phonenum}")
            return False

    # 处理信息
    try:
        summary = telecom.to_summary(important_data["responseData"]["data"])
    except Exception as e:
        add_notify(f"处理数据出错：{phonenum} - {str(e)}")
        return False
        
    if summary:
        print(f"处理完成：{phonenum}")
        CONFIG_DATA[f"summary_{phonenum}"] = summary

    # 获取流量包明细
    flux_package_str = ""
    if TELECOM_FLUX_PACKAGE:
        user_flux_package = telecom.user_flux_package()
        if user_flux_package and user_flux_package.get("responseData"):
            print(f"获取流量包明细：{phonenum}")
            packages = user_flux_package["responseData"]["data"]["productOFFRatable"][
                "ratableResourcePackages"
            ]
            for package in packages:
                package_icon = (
                    "🇨🇳" if "国内" in package["title"] 
                    else "📺" if "专用" in package["title"] 
                    else "🌎"
                )
                flux_package_str += f"\n{package_icon}{package['title']}\n"
                for product in package["productInfos"]:
                    if product["infiniteTitle"]:
                        # 无限流量
                        flux_package_str += f"""🔹[{product['title']}]{product['infiniteTitle']}{product['infiniteValue']}{product['infiniteUnit']}/无限\n"""
                    else:
                        flux_package_str += f"""🔹[{product['title']}]{product['leftTitle']}{product['leftHighlight']}{product['rightCommon']}\n"""

    # 流量字符串
    common_str = (
        f"{telecom.convert_flow(summary['commonUse'],'GB',2)} / {telecom.convert_flow(summary['commonTotal'],'GB',2)} GB"
        if summary["flowOver"] == 0
        else f"-{telecom.convert_flow(summary['flowOver'],'GB',2)} / {telecom.convert_flow(summary['commonTotal'],'GB',2)} GB"
    )
    common_str = (
        f"{common_str} {usage_status_icon(summary['commonUse'],summary['commonTotal'])}"
    )
    special_str = (
        f"{telecom.convert_flow(summary['specialUse'], 'GB', 2)} / {telecom.convert_flow(summary['specialTotal'], 'GB', 2)} GB"
        if summary["specialTotal"] > 0
        else ""
    )

    # 基本信息
    notify_str = f"""
📱 手机：{summary['phonenum']}
💰 余额：{round(summary['balance']/100,2)}元
📞 通话：{summary['voiceUsage']}{f" / {summary['voiceTotal']}" if summary['voiceTotal']>0 else ''} 分钟
🌐 总流量
  - 通用：{common_str}{f'{chr(10)}  - 专用：{special_str}' if special_str else ''}"""

    # 流量包明细
    if TELECOM_FLUX_PACKAGE and flux_package_str:
        notify_str += f"\n\n【流量包明细】\n\n{flux_package_str.strip()}"

    notify_str += f"\n\n查询时间：{summary['createTime']}"
    notify_str += "\n" + "="*30  # 分隔不同账号的信息

    add_notify(notify_str.strip())
    return True


def main():
    global CONFIG_DATA
    start_time = datetime.datetime.now()
    print(f"===============程序开始===============")
    print(f"⏰ 执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 读取配置
    if os.path.exists(CONFIG_PATH):
        print(f"⚙️ 正从 {CONFIG_PATH} 文件中读取配置")
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            CONFIG_DATA = json.load(file)
    
    # 获取多账号信息
    telecom_users = os.environ.get("TELECOM_USER", "")
    if not telecom_users:
        exit("未设置TELECOM_USER环境变量，程序退出")
        
    # 分割多账号，用&分隔
    accounts = telecom_users.split("&")
    valid_accounts = []
    
    # 验证账号格式
    for account in accounts:
        if len(account) == 17 and account[:11].isdigit() and account[11:].isdigit():
            phonenum = account[:11]
            password = account[11:]
            valid_accounts.append((phonenum, password))
        else:
            add_notify(f"账号格式错误：{account}，应为11位号码+6位密码")
    
    if not valid_accounts:
        exit("没有有效的账号信息，程序退出")
    
    print(f"共发现{len(valid_accounts)}个有效账号，开始处理...")
    
    # 逐个处理账号
    for phonenum, password in valid_accounts:
        print(f"\n===== 开始处理账号：{phonenum} =====")
        process_account(phonenum, password)
    
    # 发送汇总通知
    if NOTIFYS:
        notify_body = "\n".join(NOTIFYS)
        print(f"\n===============推送通知===============")
        send_notify("【电信套餐用量监控 - 多账号汇总】", notify_body)
        print()

    update_config()
    print(f"\n===============程序结束===============")
    print(f"⏰ 结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  运行时长: {datetime.datetime.now() - start_time}")


def update_config():
    # 更新配置
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(CONFIG_DATA, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
