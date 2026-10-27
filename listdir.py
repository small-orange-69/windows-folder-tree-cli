import os
import sys
import json
import re
import ctypes
from pathlib import Path

# Windows控制台颜色常量
FOREGROUND_RED = 0x0004
FOREGROUND_GREEN = 0x0002
FOREGROUND_BLUE = 0x0001
FOREGROUND_YELLOW = FOREGROUND_RED | FOREGROUND_GREEN
FOREGROUND_WHITE = FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE

# 获取exe/脚本所在目录
APP_PATH = Path(sys.executable if hasattr(sys, 'frozen') else __file__).parent
CONFIG_FILE = APP_PATH / "config.json"
LANG_FILE = APP_PATH / "lang.json"

# 默认配置
DEFAULT_CONFIG = {
    "default_depth": 0,
    "language": "zh",
    "default_admin": False,
    "default_debug": False,
    "max_entries_per_dir": 20,
    "whitelist": [],
    "blacklist": [],
    "list_mode": 1,
    "name_regex": "",
    "enable_regex": False
}

def set_console_color(color: int):
    """设置CMD文字颜色"""
    kernel32 = ctypes.windll.kernel32
    hConsole = kernel32.GetStdHandle(-11)
    kernel32.SetConsoleTextAttribute(hConsole, color)

def log_debug(msg: str, lang, enable_debug: bool):
    if not enable_debug:
        return
    set_console_color(FOREGROUND_WHITE)
    print(f"{lang['log_debug']} {msg}")
    set_console_color(FOREGROUND_WHITE)

def log_warn(msg: str, lang):
    set_console_color(FOREGROUND_YELLOW)
    print(f"{lang['log_warn']} {msg}")
    set_console_color(FOREGROUND_WHITE)

def log_error(msg: str, lang):
    set_console_color(FOREGROUND_RED)
    print(f"{lang['log_error']} {msg}")
    set_console_color(FOREGROUND_WHITE)

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 兼容旧配置：缺少字段自动补全默认值
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception as e:
            print(f"配置文件读取异常，使用默认配置: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_lang(lang_code: str):
    if not LANG_FILE.exists():
        log_error("lang.json not found at program directory!", None)
        sys.exit(1)
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        lang_data = json.load(f)
    if lang_code not in lang_data:
        return lang_data["en"]
    return lang_data[lang_code]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        return
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1
    )
    sys.exit(0)

def normalize_ext(ext: str) -> str:
    """规范化文件后缀：小写并确保以.开头"""
    ext = ext.strip().lower()
    if ext and not ext.startswith("."):
        ext = "." + ext
    return ext

def should_show_file(name: str, cfg, name_pattern) -> bool:
    """根据名单与正则判断文件是否显示（目录始终显示）"""
    if cfg["list_mode"] == 4:
        return False  # 文件夹模式：不显示任何文件
    ext = os.path.splitext(name)[1].lower()
    if cfg["list_mode"] == 1:
        if cfg["whitelist"] and ext not in cfg["whitelist"]:
            return False
    elif cfg["list_mode"] == 2:
        if ext in cfg["blacklist"]:
            return False
    # list_mode == 3: 不使用名单，不按后缀过滤
    if name_pattern is not None and not name_pattern.search(name):
        return False
    return True

def apply_list_edit(current: list, val: str):
    """编辑名单：支持 -add/-a 追加、-del/-d 删除，其余视为整体覆盖。返回None表示输入无效"""
    parts = val.split(None, 1)
    op = parts[0].lower() if parts else ""
    if op in ("-add", "-a", "-del", "-d"):
        if len(parts) < 2:
            return None
        items = {normalize_ext(x) for x in parts[1].split(",") if x.strip()}
        if not items:
            return None
        if op in ("-add", "-a"):
            return sorted(set(current) | items)
        return [x for x in current if x not in items]
    if not val:
        return []
    return [normalize_ext(x) for x in val.split(",") if x.strip()]

# 多参数模式参数表: 参数名 -> (配置字段, 值类型)
CLI_ARG_MAP = {
    "-depth": ("default_depth", "int"),
    "-admin": ("default_admin", "bool"),
    "-debug": ("default_debug", "bool"),
    "-maxentries": ("max_entries_per_dir", "int"),
    "-whitelist": ("whitelist", "list"),
    "-blacklist": ("blacklist", "list"),
    "-listmode": ("list_mode", "mode"),
    "-regex": ("name_regex", "regex"),
    "-enableregex": ("enable_regex", "bool"),
}

def apply_cli_args(args: list, run_cfg: dict, lang) -> bool:
    """解析 -参数 值 形式的多参数并写入run_cfg（临时生效，不保存）。返回是否全部合法"""
    i = 0
    while i < len(args):
        key = args[i].lower()
        if key not in CLI_ARG_MAP:
            log_warn(f"{lang['unknown_param']}: {args[i]}", lang)
            return False
        if i + 1 >= len(args):
            log_warn(f"{lang['missing_value']}: {args[i]}", lang)
            return False
        field, kind = CLI_ARG_MAP[key]
        val = args[i + 1]
        if kind == "int":
            try:
                num = int(val)
                if not 0 <= num <= 255:
                    raise ValueError
                run_cfg[field] = num
            except ValueError:
                log_warn(f"{lang['invalid_value']}: {val}", lang)
                return False
        elif kind == "bool":
            v = val.lower()
            if v in ("true", "1", "yes"):
                run_cfg[field] = True
            elif v in ("false", "0", "no"):
                run_cfg[field] = False
            else:
                log_warn(f"{lang['invalid_value']}: {val}", lang)
                return False
        elif kind == "list":
            run_cfg[field] = [normalize_ext(x) for x in val.split(",") if x.strip()]
        elif kind == "mode":
            if val in ("1", "2", "3", "4"):
                run_cfg[field] = int(val)
            else:
                log_warn(f"{lang['invalid_value']}: {val}", lang)
                return False
        elif kind == "regex":
            try:
                re.compile(val)
                run_cfg[field] = val
            except re.error:
                log_warn(f"{lang['invalid_regex']}: {val}", lang)
                return False
        i += 2
    return True

def print_tree(root_path: str, prefix: str = "", depth: int = 0, max_depth: int = 0, max_entries: int = 20, lang=None, enable_debug=False, cfg=None, name_pattern=None):
    log_debug(f"扫描目录: {root_path}, 当前深度:{depth}", lang, enable_debug)
    entries = list(os.scandir(root_path))
    raw_total = len(entries)
    entries = [e for e in entries if e.is_dir(follow_symlinks=False) or should_show_file(e.name, cfg, name_pattern)]
    log_debug(f"过滤后剩余条目: {len(entries)}/{raw_total}", lang, enable_debug)
    entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
    total = len(entries)

    if max_entries == 0:
        show_count = total
    else:
        show_count = min(total, max_entries)

    for idx, entry in enumerate(entries[:show_count]):
        is_last = idx == show_count -1
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{entry.name}")
        if entry.is_dir(follow_symlinks=False):
            if max_depth !=0 and depth +1 >= max_depth:
                continue
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(entry.path, new_prefix, depth+1, max_depth, max_entries, lang, enable_debug, cfg, name_pattern)

    if max_entries != 0 and total > max_entries:
        remain = total - max_entries
        print(f"{prefix}└── {lang['more_entries_hint'].format(remain)}")

def setting_mode(lang, cfg):
    while True:
        print("\n" + lang["menu_title"])
        print(lang["opt1"], f"[{cfg['default_depth']}]")
        print(lang["opt2"], f"[{cfg['language']}]")
        print(f"  {lang['available_lang_tip']} {lang['lang_list']}")
        print(lang["opt3"], f"[{lang['admin_true'] if cfg['default_admin'] else lang['admin_false']}]")
        print(lang["opt4"], f"[{lang['debug_true'] if cfg['default_debug'] else lang['debug_false']}]")
        print(lang["opt5"], f"[{cfg['max_entries_per_dir']}]")
        whitelist_disp = ", ".join(cfg["whitelist"]) if cfg["whitelist"] else lang["list_empty"]
        blacklist_disp = ", ".join(cfg["blacklist"]) if cfg["blacklist"] else lang["list_empty"]
        print(lang["opt6"], f"[{whitelist_disp}]")
        print(lang["opt7"], f"[{blacklist_disp}]")
        mode_names = {1: lang["mode_whitelist"], 2: lang["mode_blacklist"], 3: lang["mode_none"], 4: lang["mode_folder"]}
        print(lang["opt8"], f"[{mode_names.get(cfg['list_mode'], '?')}]")
        print(lang["opt9"], f"[{cfg['name_regex'] if cfg['name_regex'] else lang['regex_empty']}]")
        print(lang["opt10"], f"[{lang['regex_true'] if cfg['enable_regex'] else lang['regex_false']}]")

        user_in = input("\n" + lang["input_prompt"]).strip()
        if user_in.lower() == "q":
            print(lang["exit_setting"])
            break
        if user_in == "1":
            val = input(lang["input_val_prompt"]).strip()
            try:
                num = int(val)
                if 0 <= num <=255:
                    cfg["default_depth"] = num
                    save_config(cfg)
                    print(lang["save_success"])
                else:
                    log_warn(lang["invalid_value"], lang)
            except ValueError:
                log_warn(lang["invalid_value"], lang)
        elif user_in == "2":
            val = input(lang["input_val_prompt"]).strip()
            valid_list = lang["lang_list"]
            if val in valid_list:
                cfg["language"] = val
                save_config(cfg)
                print(lang["save_success"])
            else:
                log_warn(lang["invalid_value"], lang)
        elif user_in == "3":
            val = input(lang["input_val_prompt"]).strip().lower()
            if val in ["true", "1", "yes"]:
                cfg["default_admin"] = True
                save_config(cfg)
                print(lang["save_success"])
            elif val in ["false", "0", "no"]:
                cfg["default_admin"] = False
                save_config(cfg)
                print(lang["save_success"])
            else:
                log_warn(lang["invalid_value"], lang)
        elif user_in == "4":
            val = input(lang["input_val_prompt"]).strip().lower()
            if val in ["true", "1", "yes"]:
                cfg["default_debug"] = True
                save_config(cfg)
                print(lang["save_success"])
            elif val in ["false", "0", "no"]:
                cfg["default_debug"] = False
                save_config(cfg)
                print(lang["save_success"])
            else:
                log_warn(lang["invalid_value"], lang)
        elif user_in == "5":
            val = input(lang["input_val_prompt"]).strip()
            try:
                num = int(val)
                if 0 <= num <=255:
                    cfg["max_entries_per_dir"] = num
                    save_config(cfg)
                    print(lang["save_success"])
                else:
                    log_warn(lang["invalid_value"], lang)
            except ValueError:
                log_warn(lang["invalid_value"], lang)
        elif user_in == "6":
            val = input(lang["input_list_prompt"]).strip()
            new_list = apply_list_edit(cfg["whitelist"], val)
            if new_list is None:
                log_warn(lang["invalid_value"], lang)
            else:
                cfg["whitelist"] = new_list
                save_config(cfg)
                print(lang["save_success"])
        elif user_in == "7":
            val = input(lang["input_list_prompt"]).strip()
            new_list = apply_list_edit(cfg["blacklist"], val)
            if new_list is None:
                log_warn(lang["invalid_value"], lang)
            else:
                cfg["blacklist"] = new_list
                save_config(cfg)
                print(lang["save_success"])
        elif user_in == "8":
            val = input(lang["input_val_prompt"]).strip()
            if val in ["1", "2", "3", "4"]:
                cfg["list_mode"] = int(val)
                save_config(cfg)
                print(lang["save_success"])
            else:
                log_warn(lang["invalid_value"], lang)
        elif user_in == "9":
            val = input(lang["input_regex_prompt"]).strip()
            if val == "":
                cfg["name_regex"] = ""
                save_config(cfg)
                print(lang["save_success"])
            else:
                try:
                    re.compile(val)
                    cfg["name_regex"] = val
                    save_config(cfg)
                    print(lang["save_success"])
                except re.error:
                    log_warn(lang["invalid_regex"], lang)
        elif user_in == "10":
            val = input(lang["input_val_prompt"]).strip().lower()
            if val in ["true", "1", "yes"]:
                cfg["enable_regex"] = True
                save_config(cfg)
                print(lang["save_success"])
            elif val in ["false", "0", "no"]:
                cfg["enable_regex"] = False
                save_config(cfg)
                print(lang["save_success"])
            else:
                log_warn(lang["invalid_value"], lang)
        else:
            log_warn(lang["invalid_id"], lang)

def main():
    cfg = load_config()
    lang = load_lang(cfg["language"])
    args = sys.argv[1:]

    # run_cfg 为运行时生效配置：多参数模式的临时覆盖写入此处，不影响config.json
    run_cfg = cfg.copy()
    force_admin = False
    enable_debug = cfg["default_debug"]

    if len(args) >=1:
        first_arg = args[0].lower()
        if first_arg == "set":
            setting_mode(lang, cfg)
            return
        elif first_arg in ("help", "-h", "--help"):
            print(lang["help_text"])
            return
        elif first_arg.startswith("-"):
            # 多参数模式：与旧版一致，传参时不默认强制管理员
            run_cfg["default_admin"] = False
            if not apply_cli_args(args, run_cfg, lang):
                print(lang["help_hint"])
                return
            force_admin = run_cfg["default_admin"]
            enable_debug = run_cfg["default_debug"]
        elif first_arg == "admin":
            force_admin = True
        elif first_arg == "debug":
            enable_debug = True
        else:
            try:
                num = int(first_arg)
                if 0 <= num <=255:
                    run_cfg["default_depth"] = num
            except ValueError:
                log_warn(f"未知参数 {first_arg}", lang)
    else:
        force_admin = cfg["default_admin"]

    log_debug(f"启动参数: {sys.argv}", lang, enable_debug)
    log_debug(f"生效配置: {run_cfg}", lang, enable_debug)

    if force_admin and not is_admin():
        print(lang["need_admin"])
        run_as_admin()

    cwd = os.getcwd()
    name_pattern = None
    if run_cfg["enable_regex"] and run_cfg["name_regex"]:
        try:
            name_pattern = re.compile(run_cfg["name_regex"])
        except re.error:
            log_warn(lang["invalid_regex"], lang)
            name_pattern = None
    print(f"📂 {lang['current_dir']}: {cwd}")
    print_tree(
        cwd,
        max_depth=run_cfg["default_depth"],
        max_entries=run_cfg["max_entries_per_dir"],
        lang=lang,
        enable_debug=enable_debug,
        cfg=run_cfg,
        name_pattern=name_pattern
    )

if __name__ == "__main__":
    main()
