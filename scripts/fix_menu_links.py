#!/usr/bin/env python3
"""
修复模板中的菜单链接问题
"""
import os
import re

def fix_menu_links(directory='templates'):
    """
    修复模板中的菜单链接
    
    参数:
        directory: 模板目录
    """
    # 定义需要修复的链接映射
    link_fixes = {
        'href="/dashboard"': 'href="{{ url_for(\'dashboard.index\') }}"',
        'href="/department-analysis"': 'href="{{ url_for(\'analysis.department_analysis\') }}"',
        'href="/financial-analysis"': 'href="{{ url_for(\'analysis.financial_analysis\') }}"',
        'href="/patient-analysis"': 'href="{{ url_for(\'analysis.patient_analysis\') }}"',
        'href="/doctor-performance"': 'href="{{ url_for(\'analysis.doctor_performance\') }}"',
        'href="/drg-analysis"': 'href="{{ url_for(\'analysis.drg_analysis\') }}"',
        'href="/ai-chat"': 'href="{{ url_for(\'ai_chat.index\') }}"',
        'href="/user-management"': 'href="{{ url_for(\'settings.user_management\') }}"',
        'href="/system-settings"': 'href="{{ url_for(\'settings.index\') }}"',
        'href="/help"': 'href="{{ url_for(\'settings.help\') }}"',
        'href="/settings"': 'href="{{ url_for(\'settings.index\') }}"',
        'href="/profile"': 'href="{{ url_for(\'auth.profile\') }}"',
        'href="/logout"': 'href="{{ url_for(\'auth.logout\') }}"'
    }
    
    # 同时也修复请求路径检查
    path_fixes = {
        'request.path == \'/dashboard\'': 'request.endpoint == \'dashboard.index\'',
        'request.path == \'/department-analysis\'': 'request.endpoint == \'analysis.department_analysis\'',
        'request.path == \'/financial-analysis\'': 'request.endpoint == \'analysis.financial_analysis\'',
        'request.path == \'/patient-analysis\'': 'request.endpoint == \'analysis.patient_analysis\'',
        'request.path == \'/doctor-performance\'': 'request.endpoint == \'analysis.doctor_performance\'',
        'request.path == \'/drg-analysis\'': 'request.endpoint == \'analysis.drg_analysis\'',
        'request.path == \'/ai-chat\'': 'request.endpoint == \'ai_chat.index\'',
        'request.path == \'/user-management\'': 'request.endpoint == \'settings.user_management\'',
        'request.path == \'/system-settings\'': 'request.endpoint == \'settings.index\'',
        'request.path == \'/help\'': 'request.endpoint == \'settings.help\'',
        '\'/analysis\' in request.path': '\'analysis.\' in request.endpoint'
    }
    
    # 遍历模板目录中的所有HTML文件
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                print(f"处理文件: {file_path}")
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 应用链接修复
                modified = False
                for old_link, new_link in link_fixes.items():
                    if old_link in content:
                        content = content.replace(old_link, new_link)
                        modified = True
                        print(f"  - 修复链接: {old_link} -> {new_link}")
                
                # 应用路径检查修复
                for old_path, new_path in path_fixes.items():
                    if old_path in content:
                        content = content.replace(old_path, new_path)
                        modified = True
                        print(f"  - 修复路径检查: {old_path} -> {new_path}")
                
                # 如果有修改，写回文件
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  - 已保存修改")

if __name__ == '__main__':
    fix_menu_links()
    print("菜单链接修复完成！") 