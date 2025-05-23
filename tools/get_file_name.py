import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

def scan_dir_for_exe(dir_path):
    found = []
    subdirs = []
    try:
        with os.scandir(dir_path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.lower().endswith('.exe'):
                    name = entry.name[:-4]
                    if is_ascii(name):
                        found.append(entry.path)
                elif entry.is_dir(follow_symlinks=False):
                    subdirs.append(entry.path)
    except:
        pass
    return found, subdirs

def threaded_scan(start_path, max_workers=16):
    result = []
    to_scan = [start_path]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        while to_scan or futures:
            while to_scan and len(futures) < max_workers * 2:
                path = to_scan.pop()
                futures.append(executor.submit(scan_dir_for_exe, path))

            done_futures = []
            for future in as_completed(futures, timeout=None):
                try:
                    found_files, subdirs = future.result()
                    result.extend(found_files)
                    to_scan.extend(subdirs)
                except:
                    continue
                done_futures.append(future)
                if len(done_futures) >= len(futures):
                    break

            futures = [f for f in futures if f not in done_futures]

    return result

if __name__ == '__main__':
    c_drive = 'C:\\'
    output_file = 'ascii_exe_files_fast.txt'

    print('正在扫描 C 盘，请稍等...')
    found_files = threaded_scan(c_drive)

    # 提取文件名并去重
    unique_names = sorted(set(os.path.basename(path) for path in found_files))

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for name in unique_names:
            f.write(name + '\n')

    print(f'完成！共找到 {len(unique_names)} 个唯一 ASCII 名称的 .exe 文件，结果保存在 {output_file}')
