import requests
import re
import csv
import time
import sys
import random

# 🔥 核心特制正则表达式：
# ^[a-z]        -> 必须以小写字母开头
# [a-z0-9]{2,17}$ -> 后面接 2 到 17 位的纯小写字母或数字（总长度正好 3 到 18 位）
STRICT_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9]{2,17}$')

# 初始化 Session
session = requests.Session()
session.trust_env = False  # 强力直连！防止因 Windows/系统代理问题导致脚本假死卡住 (•̀ω•́)✧

session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://space.bilibili.com/',
    'Connection': 'close'
})

def check_uid(uid):
    detail = {
        "UID": uid,
        "昵称": "获取失败",
        "关注数": "-",
        "粉丝数": "-",
        "账号等级": "-",
        "是否符合": "❌ 不符合"
    }

    try:
        # 🛡️ 延长基本间隔，降低单 IP 访问频率确保长期稳定安全
        time.sleep(random.uniform(2.0, 5.0))
        
        url = f"https://api.bilibili.com/x/web-interface/card?mid={uid}"
        response = session.get(url, timeout=3).json()
        
        if response.get("code") == 0:
            card_data = response.get("data", {}).get("card", {})
            if not card_data:
                detail["是否符合"] = "❌ 账号不存在"
                return detail, None
                
            name = card_data.get("name", "")
            level = card_data.get("level_info", {}).get("current_level", 0)
            fans = card_data.get("fans", 0)
            following = card_data.get("attention", 0)
            
            detail["昵称"] = name
            detail["关注数"] = following
            detail["粉丝数"] = fans
            detail["账号等级"] = f"Lv.{level}"
            
            # 多重条件联合极致过滤
            is_name_ok = bool(STRICT_NAME_PATTERN.match(name))
            is_level_ok = (level == 0)
            is_relation_ok = (following == 0 and fans == 0)
            
            if is_name_ok and is_level_ok and is_relation_ok:
                detail["是否符合"] = "✅ 符合要求"
                res_data = {
                    "UID": uid,
                    "昵称": name,
                    "关注数": following,
                    "粉丝数": fans,
                    "账号等级": level
                }
                return detail, res_data
            else:
                reasons = []
                if not is_name_ok: reasons.append("名字不符(要求字母开头|小写英数|3-18位)")
                if not is_level_ok: reasons.append(f"等级Lv.{level}不符(要求Lv.0)")
                if not is_relation_ok: reasons.append(f"关注{following}/粉丝{fans}(要求双0)")
                detail["是否符合"] = f"❌ 不符合 ({'|'.join(reasons)})"
                
        elif response.get("code") == -412:
            # 💤 触发频繁拦截时，拉长强制休息时间，防止 IP 被硬封
            cool_down = random.randint(30, 60)
            detail["是否符合"] = f"⚠️ 触发频繁拦截，强制冷却 {cool_down} 秒..."
            time.sleep(cool_down)
            
    except requests.exceptions.Timeout:
        detail["是否符合"] = "⚠️ 请求超时（网络或代理问题）"
    except Exception as e:
        detail["是否符合"] = f"⚠️ 网络错误: {str(e)}"
        
    return detail, None

def get_config():
    """获取用户自定义的 UID 区间和后缀限制"""
    start, end, suffix = None, None, ""
    
    if len(sys.argv) in (3, 4):
        try:
            start = int(sys.argv[1])
            end = int(sys.argv[2])
            if len(sys.argv) == 4:
                suffix = sys.argv[3].strip()
            if start <= end and (not suffix or suffix.isdigit()):
                return start, end, suffix
        except ValueError:
            pass
        print("⚠️ 命令行参数解析失败，转为手动输入模式...")

    while True:
        try:
            if start is None or end is None:
                start = int(input("⌨️ 请输入【开始】的 UID: ").strip())
                end = int(input("⌨️ 请输入【结束】的 UID: ").strip())
                if start > end:
                    print("❌ 结束 UID 必须大于或等于开始 UID，请重新输入区间！")
                    start, end = None, None
                    continue
            
            suffix_input = input("⌨️ 请输入【尾号后缀】(如88，直接回车代表搜全部): ").strip()
            if suffix_input and not suffix_input.isdigit():
                print("❌ 尾号后缀必须是纯数字，请重新输入后缀！")
                continue
            
            return start, end, suffix_input
        except ValueError:
            print("❌ 输入格式错误，UID 必须为纯数字！")
            start, end = None, None

def main():
    print("=" * 65)
    print("   Bilibili 珍稀UID全量通用扫描器 (双0|严格0级|字母开头3-18位)   ")
    print("=" * 65)
    sys.stdout.flush() 
    
    start_uid, end_uid, suffix = get_config()
    
    all_uids = [uid for uid in range(start_uid, end_uid + 1) if str(uid).endswith(suffix)]
    total_tasks = len(all_uids)
    completed_tasks = 0
    hit_results = []
    
    if total_tasks == 0:
        print("❌ 当前区间内没有符合该尾号后缀的 UID，程序退出。")
        return
        
    suffix_msg = f"指定尾号【{suffix}】" if suffix else "全量尾号"
    print(f"\n📢 目标：扫描从 {start_uid} 到 {end_uid} 中所有符合 {suffix_msg} 的 UID")
    print(f"📊 实际需要请求的目标总数：{total_tasks} 个")
    print(f"🚀 安全防封模式已启动，正在准备第一次请求...\n")
    sys.stdout.flush()
    
    for uid in all_uids:
        detail, hit_data = check_uid(uid)
        completed_tasks += 1
        percent = (completed_tasks / total_tasks) * 100
        
        log_str = f"🔍 [UID:{detail['UID']}] 昵称:{detail['昵称']:<12} 等级:{detail['账号等级']:<5} 关注:{detail['关注数']:<4} 粉丝:{detail['粉丝数']:<4} 状态:{detail['是否符合']}"
        clear_len = max(130, len(log_str) + 10)
        sys.stdout.write("\r" + " " * clear_len + "\r")
        
        print(log_str)
        sys.stdout.flush() 
        
        if hit_data:
            hit_results.append(hit_data)
        
        sys.stdout.write(f"\r⏳ 匹配进度: {percent:2.3f}% ({completed_tasks}/{total_tasks}) 已捕获: {len(hit_results)} 个")
        sys.stdout.flush()

    print("\n\n" + "=" * 65)
    print(" 🏁 扫描结束！完全符合要求的账号汇总如下：")
    print("=" * 65)

    if hit_results:
        hit_results.sort(key=lambda x: x["UID"])
        
        print(f"{'UID':<12}\t{'昵称':<15}\t{'等级':<6}\t{'关注':<6}\t{'粉丝':<6}")
        print("-" * 65)
        for r in hit_results:
            print(f"{r['UID']:<12}\t{r['昵称']:<15}\tLv.{r['账号等级']:<4}\t{r['关注数']:<6}\t{r['粉丝数']:<6}")
            
        suffix_flag = f"_end{suffix}" if suffix else "_all"
        filename = f"bili_scan{suffix_flag}_{start_uid}_{end_uid}.csv"
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["UID", "昵称", "关注数", "粉丝数", "账号等级"])
            writer.writeheader()
            writer.writerows(hit_results)
        print("=" * 65)
        print(f"🎉 结果已打包成功，保存在: {filename}")
    else:
        print(f"❌ 区间内符合尾号【{suffix if suffix else '全部'}】的账号扫描完毕，未发现完美符合条件的账号。")

if __name__ == "__main__":
    main()