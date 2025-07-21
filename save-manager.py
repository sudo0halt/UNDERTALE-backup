#!/usr/bin/env python3
"""
UNDERTALE セーブデータ管理ツール

セーブデータのバックアップ・復元・管理を行うツール
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

class UndertaleeSaveManager:
    def __init__(self):
        """初期化：基本的なパスと設定を設定"""
        self.base_dir = Path(__file__).parent
        self.saves_dir = self.base_dir / "saves"
        self.current_save_dir = self.saves_dir / "current"
        self.backups_dir = self.saves_dir / "backups"
        self.config_file = self.base_dir / "config.json"
        
        # UNDERTALEのセーブファイル一覧
        self.save_files = ["file0", "file8", "file9", "undertale.ini", "config.ini"]
    
    def load_config(self):
        """設定ファイルを読み込み"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"設定ファイルの読み込みエラー: {e}")
                return {}
        return {}
    
    def save_config(self, config):
        """設定ファイルを保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"設定ファイルの保存エラー: {e}")
    
    def detect_game_path(self):
        """UNDERTALEのインストールパスを自動検出"""
        print("UNDERTALEのインストールパスを自動検出しています...")
        
        possible_paths = []
        
        if os.name == 'nt':  # Windows
            # Windows標準パス
            appdata = os.environ.get('LOCALAPPDATA')
            if appdata:
                possible_paths.append(Path(appdata) / "UNDERTALE")
        else:  # Linux/WSL
            # WSL環境でのWindowsパス
            win_users = Path("/mnt/c/Users")
            if win_users.exists():
                for user_dir in win_users.glob("*/"):
                    undertale_path = user_dir / "AppData/Local/UNDERTALE"
                    if undertale_path.exists():
                        possible_paths.append(undertale_path)
        
        # 検出されたパスをチェック
        for path in possible_paths:
            if path.exists() and any((path / filename).exists() for filename in self.save_files):
                print(f"検出されました: {path}")
                return str(path)
        
        print("自動検出できませんでした")
        return None
    
    def ask_game_path(self):
        """ユーザーにセーブデータの場所を質問"""
        print("\n=== セーブデータの場所を設定 ===")
        
        # 自動検出を試行
        auto_detected = self.detect_game_path()
        if auto_detected:
            while True:
                answer = input(f"検出されたパス '{auto_detected}' を使用しますか？ (y/n): ").strip().lower()
                if answer in ['y', 'yes']:
                    return auto_detected
                elif answer in ['n', 'no']:
                    break
                else:
                    print("y または n で回答してください")
        
        # 手動入力
        while True:
            path = input("UNDERTALEのセーブデータフォルダのパスを入力してください: ").strip()
            if not path:
                print("パスを入力してください")
                continue
            
            path_obj = Path(path)
            if not path_obj.exists():
                print("指定されたパスが存在しません")
                continue
            
            # セーブファイルの存在確認
            found_files = []
            for filename in self.save_files:
                if (path_obj / filename).exists():
                    found_files.append(filename)
            
            if found_files:
                print(f"以下のファイルが見つかりました: {', '.join(found_files)}")
                return str(path_obj)
            else:
                print("UNDERTALEのセーブファイルが見つかりません")
                retry = input("別のパスを試しますか？ (y/n): ").strip().lower()
                if retry not in ['y', 'yes']:
                    return None
    
    def clear_current_saves(self):
        """現在のセーブディレクトリをクリア"""
        print("現在のセーブディレクトリをクリアしています...")
        
        if self.current_save_dir.exists():
            # ディレクトリ内のファイルを削除
            for file_path in self.current_save_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    print(f"削除: {file_path.name}")
        else:
            # ディレクトリが存在しない場合は作成
            self.current_save_dir.mkdir(parents=True)
        
        print("クリア完了")
    
    def copy_save_files(self, source_path):
        """セーブファイルをsaves/current/にコピー"""
        print(f"\nセーブファイルを {source_path} からコピーしています...")
        
        source_dir = Path(source_path)
        copied_count = 0
        
        for filename in self.save_files:
            source_file = source_dir / filename
            if source_file.exists():
                destination = self.current_save_dir / filename
                try:
                    shutil.copy2(source_file, destination)
                    print(f"コピー: {filename}")
                    copied_count += 1
                except IOError as e:
                    print(f"コピーエラー ({filename}): {e}")
            else:
                print(f"スキップ: {filename} (ファイルが見つかりません)")
        
        print(f"\n{copied_count} ファイルをコピーしました")
        return copied_count > 0
    
    def init_setup(self):
        """初期化処理のメイン関数"""
        print("=== UNDERTALE セーブデータ管理ツール - 初期化 ===")
        
        # 必要なディレクトリ構造を確認・作成
        self.saves_dir.mkdir(exist_ok=True)
        self.current_save_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        
        # 現在の設定を読み込み
        config = self.load_config()
        
        # セーブデータの場所を質問
        game_path = self.ask_game_path()
        if not game_path:
            print("初期化が中断されました")
            return False
        
        # 現在のセーブディレクトリをクリア
        self.clear_current_saves()
        
        # セーブファイルをコピー
        if not self.copy_save_files(game_path):
            print("セーブファイルのコピーに失敗しました")
            return False
        
        # 設定を保存
        config['game_path'] = game_path
        config['initialized'] = True
        self.save_config(config)
        
        print("\n=== 初期化完了 ===")
        print(f"ゲームパス: {game_path}")
        print(f"設定保存: {self.config_file}")
        print("\npython save-manager.py でツールを起動できます")
        
        return True
    
    def main_menu(self):
        """メインメニューの表示（ダミー実装）"""
        # 設定の確認
        config = self.load_config()
        if not config.get('initialized', False):
            print("まず初期化を行ってください:")
            print("python save-manager.py --init")
            return
        
        print("=== UNDERTALE セーブデータ管理ツール ===")
        print(f"ゲームパス: {config.get('game_path', '未設定')}")
        print("対話メニュー - 開発中!")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="UNDERTALE セーブデータ管理ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python save-manager.py --init    # 初期化
  python save-manager.py           # 通常起動
        """
    )
    parser.add_argument("--init", action="store_true", help="初期化を実行")
    
    args = parser.parse_args()
    
    manager = UndertaleeSaveManager()
    
    try:
        if args.init:
            manager.init_setup()
        else:
            manager.main_menu()
    except KeyboardInterrupt:
        print("\n\n処理が中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

if __name__ == "__main__":
    main()