import pefile
import struct
from io import BytesIO
import csv
import os
import glob

def get_version_info(pe_file_path):
    try:
        pe = pefile.PE(pe_file_path)
        if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            return {}

        for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if resource_type.struct.Id == pefile.RESOURCE_TYPE['RT_VERSION']:
                for resource_entry in resource_type.directory.entries:
                    for resource_data in resource_entry.directory.entries:
                        data_rva = resource_data.data.struct.OffsetToData
                        size = resource_data.data.struct.Size
                        data = pe.get_data(data_rva, size)
                        return parse_version_info(data)
        return {}
    except Exception as e:
        print(f"[ERROR] {pe_file_path}: {e}")
        return {}

def parse_version_info(data):
    version_info = BytesIO(data)
    result = {}

    try:
        wLength, wValueLength, wType = struct.unpack('<HHH', version_info.read(6))
        szKey = read_unicode_string(version_info)
        if szKey != "VS_VERSION_INFO":
            return {}

        align_to_4_bytes(version_info)

        if wValueLength > 0:
            version_info.read(wValueLength)
            align_to_4_bytes(version_info)

        while version_info.tell() < len(data):
            start_pos = version_info.tell()
            wLength, wValueLength, wType = struct.unpack('<HHH', version_info.read(6))
            if wLength == 0:
                break
            szKey = read_unicode_string(version_info)
            align_to_4_bytes(version_info)

            if szKey == "StringFileInfo":
                result.update(parse_string_file_info(version_info, start_pos + wLength))

            version_info.seek(start_pos + wLength, 0)

    except Exception as e:
        print(f"Error parsing version info structure: {e}")
    return result

def parse_string_file_info(version_info, end_pos):
    result = {}
    try:
        while version_info.tell() < end_pos:
            start_pos = version_info.tell()
            wLength, wValueLength, wType = struct.unpack('<HHH', version_info.read(6))
            if wLength == 0:
                break
            read_unicode_string(version_info)  # Skip language code
            align_to_4_bytes(version_info)

            table_end = start_pos + wLength
            while version_info.tell() < table_end:
                string_start = version_info.tell()
                if string_start + 6 > table_end:
                    break
                wLength, wValueLength, wType = struct.unpack('<HHH', version_info.read(6))
                if wLength == 0:
                    break
                string_key = read_unicode_string(version_info)
                align_to_4_bytes(version_info)
                value_bytes = version_info.read(wValueLength * 2)
                if len(value_bytes) != wValueLength * 2:
                    break
                value = value_bytes.decode('utf-16le').rstrip('\x00')
                result[string_key] = value
                version_info.seek(string_start + wLength, 0)
                align_to_4_bytes(version_info)

            version_info.seek(table_end, 0)

    except Exception as e:
        print(f"Error parsing StringFileInfo: {e}")
    return result

def read_unicode_string(stream):
    result = []
    while True:
        char = stream.read(2)
        if not char or char == b'\x00\x00':
            break
        result.append(char)
    return b''.join(result).decode('utf-16le')

def align_to_4_bytes(stream):
    pos = stream.tell()
    padding = (4 - (pos % 4)) % 4
    stream.seek(pos + padding)

def batch_parse_directory(directory_path, output_csv="output.csv"):
    pe_files = glob.glob(os.path.join(directory_path, "*.exe")) + glob.glob(os.path.join(directory_path, "*.dll"))

    all_rows = []
    all_keys = set(["FileName"])  # 初始包含 FilePath

    for file_path in pe_files:
        info = get_version_info(file_path)
        info_row = {"FileName": os.path.basename(file_path)}
        for key, value in info.items():
            info_row[key] = value
            all_keys.add(key)
        all_rows.append(info_row)
        print(f"[OK] Parsed: {file_path}")

    # 按字段名排序输出（可选）
    sorted_keys = ["FileName"] + sorted(all_keys - {"FileName"})

    # 写入 CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_keys)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

# 示例用法
if __name__ == "__main__":
    target_dir = r"C:\Windows\System32"  # 替换为你的目录
    batch_parse_directory(target_dir, output_csv="pe_version_info.csv")
