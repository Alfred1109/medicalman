"""
应用测试文件
"""
import os
import sys
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.database import Database

class AppTestCase(unittest.TestCase):
    """应用测试用例"""
    
    def setUp(self):
        """测试前准备"""
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['DATABASE_PATH'] = ':memory:'  # 使用内存数据库
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建测试数据
        self._create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        self.app_context.pop()
    
    def _create_test_data(self):
        """创建测试数据"""
        # 创建用户表
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            email TEXT,
            department TEXT
        )
        ''')
        
        # 创建测试用户
        from app.models.user import User
        test_password_hash = User.hash_password('Test123!')
        cursor.execute('''
        INSERT INTO users (username, password_hash, role, email, department)
        VALUES (?, ?, ?, ?, ?)
        ''', ('test_user', test_password_hash, 'user', 'test@example.com', '测试部门'))
        
        conn.commit()
        conn.close()
    
    def test_home_page(self):
        """测试首页"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # 应该重定向到登录页面
    
    def test_login_page(self):
        """测试登录页面"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())
    
    def test_login(self):
        """测试登录功能"""
        # 模拟验证码
        with self.client.session_transaction() as session:
            session['captcha'] = 'TEST'
        
        # 提交登录表单
        response = self.client.post('/login', data={
            'username': 'test_user',
            'password': 'Test123!',
            'captcha': 'TEST'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'dashboard', response.data.lower())
    
    def test_invalid_login(self):
        """测试无效登录"""
        # 模拟验证码
        with self.client.session_transaction() as session:
            session['captcha'] = 'TEST'
        
        # 提交登录表单
        response = self.client.post('/login', data={
            'username': 'test_user',
            'password': 'WrongPassword',
            'captcha': 'TEST'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'error', response.data.lower())

if __name__ == '__main__':
    unittest.main() 