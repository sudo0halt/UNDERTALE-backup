#!/usr/bin/env python3
"""
UNDERTALE Save Data Manager
Copyright (C) 2025 sudo0halt

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

UNDERTALE is a trademark of Toby Fox.

セーブデータのバックアップ・復元・管理を行うツール
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

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
    
    def clear_directory(self, directory):
        """指定されたディレクトリ内のファイルをクリア"""
        if directory.exists():
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        else:
            directory.mkdir(parents=True)
    
    def copy_save_files(self, source_path, destination_path, description=""):
        """セーブファイルをコピー"""
        source_dir = Path(source_path)
        dest_dir = Path(destination_path)
        
        # 宛先ディレクトリを作成
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        
        for filename in self.save_files:
            source_file = source_dir / filename
            if source_file.exists():
                destination_file = dest_dir / filename
                try:
                    shutil.copy2(source_file, destination_file)
                    if description:
                        print(f"コピー: {filename} {description}")
                    copied_count += 1
                except IOError as e:
                    print(f"コピーエラー ({filename}): {e}")
        
        return copied_count
    
    def get_backup_list(self):
        """バックアップの一覧を取得（日時順でソート）"""
        if not self.backups_dir.exists():
            return []
        
        backups = []
        for backup_dir in self.backups_dir.iterdir():
            if backup_dir.is_dir():
                # ディレクトリ内にセーブファイルがあるかチェック
                has_saves = any((backup_dir / filename).exists() for filename in self.save_files)
                if has_saves:
                    backups.append({
                        'name': backup_dir.name,
                        'path': backup_dir,
                        'modified': backup_dir.stat().st_mtime
                    })
        
        # 更新日時順でソート（新しい順）
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups
    
    def display_save_list(self):
        """セーブ一覧を表示"""
        print("\n=== セーブデータ一覧 ===")
        
        # 現在のセーブ確認
        current_files = []
        if self.current_save_dir.exists():
            for filename in self.save_files:
                if (self.current_save_dir / filename).exists():
                    current_files.append(filename)
        
        print(f"現在のセーブ: {len(current_files)} ファイル")
        if current_files:
            print(f"  ファイル: {', '.join(current_files)}")
        
        # バックアップ一覧
        backups = self.get_backup_list()
        print(f"\nバックアップ: {len(backups)} 個")
        
        if backups:
            for i, backup in enumerate(backups, 1):
                # 日時を読みやすい形式に変換
                modified_time = datetime.fromtimestamp(backup['modified']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {i:2d}. {backup['name']} ({modified_time})")
        else:
            print("  バックアップはありません")
    
    def create_backup(self):
        """バックアップを作成"""
        print("\n=== バックアップ作成 ===")
        
        config = self.load_config()
        game_path = config.get('game_path')
        if not game_path:
            print("ゲームパスが設定されていません")
            return
        
        # ステップ1: ゲームフォルダ → saves/current/
        print("ステップ1: ゲームフォルダから最新セーブを取得...")
        self.clear_directory(self.current_save_dir)
        copied = self.copy_save_files(game_path, self.current_save_dir)
        
        if copied == 0:
            print("ゲームフォルダにセーブファイルが見つかりません")
            return
        
        print(f"{copied} ファイルを取得しました")
        
        # ステップ2: バックアップ名を決定
        while True:
            backup_name = input("\nバックアップ名を入力してください (空欄で自動生成): ").strip()
            if not backup_name:
                # 自動生成: 日時ベース
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
                break
            
            # バックアップ名の重複チェック
            backup_path = self.backups_dir / backup_name
            if backup_path.exists():
                print(f"'{backup_name}' は既に存在します")
                overwrite = input("上書きしますか？ (y/n): ").strip().lower()
                if overwrite in ['y', 'yes']:
                    break
            else:
                break
        
        # ステップ3: saves/current/ → saves/backups/[名前]
        print(f"ステップ2: '{backup_name}' として保存...")
        backup_path = self.backups_dir / backup_name
        
        # 既存のバックアップディレクトリを削除（上書きの場合）
        if backup_path.exists():
            shutil.rmtree(backup_path)
        
        copied = self.copy_save_files(self.current_save_dir, backup_path)
        print(f"バックアップ作成完了: {backup_name} ({copied} ファイル)")
    
    def restore_backup(self):
        """バックアップから復元"""
        print("\n=== バックアップから復元 ===")
        
        # バックアップ一覧を取得
        backups = self.get_backup_list()
        if not backups:
            print("復元可能なバックアップがありません")
            return
        
        # バックアップ一覧を表示
        print("復元可能なバックアップ:")
        for i, backup in enumerate(backups, 1):
            modified_time = datetime.fromtimestamp(backup['modified']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {i:2d}. {backup['name']} ({modified_time})")
        
        # ユーザーに選択させる
        while True:
            try:
                choice = input(f"\n復元するバックアップ番号を入力してください (1-{len(backups)}, 0でキャンセル): ").strip()
                if choice == "0":
                    print("復元をキャンセルしました")
                    return
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(backups):
                    selected_backup = backups[choice_num - 1]
                    break
                else:
                    print(f"1から{len(backups)}の間で入力してください")
            except ValueError:
                print("数値を入力してください")
        
        # 確認
        print(f"\n'{selected_backup['name']}' を復元します")
        confirm = input("現在のセーブデータとゲーム内データが上書きされます。続行しますか？ (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("復元をキャンセルしました")
            return
        
        config = self.load_config()
        game_path = config.get('game_path')
        if not game_path:
            print("ゲームパスが設定されていません")
            return
        
        # ステップ1: バックアップ → saves/current/
        print("ステップ1: バックアップをcurrentに復元...")
        self.clear_directory(self.current_save_dir)
        copied1 = self.copy_save_files(selected_backup['path'], self.current_save_dir)
        
        # ステップ2: saves/current/ → ゲームフォルダ
        print("ステップ2: ゲームフォルダに適用...")
        copied2 = self.copy_save_files(self.current_save_dir, game_path)
        
        print(f"復元完了: {selected_backup['name']} ({copied2} ファイルをゲームに適用)")
    
    def delete_backup(self):
        """バックアップを削除"""
        print("\n=== バックアップ削除 ===")
        
        # バックアップ一覧を取得
        backups = self.get_backup_list()
        if not backups:
            print("削除可能なバックアップがありません")
            return
        
        # バックアップ一覧を表示
        print("削除可能なバックアップ:")
        for i, backup in enumerate(backups, 1):
            modified_time = datetime.fromtimestamp(backup['modified']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {i:2d}. {backup['name']} ({modified_time})")
        
        # 複数選択または単体選択
        print("\n削除方法を選択してください:")
        print("  a. 複数選択で削除")
        print("  s. 単体選択で削除")
        print("  0. キャンセル")
        
        mode = input("\n選択してください (a/s/0): ").strip().lower()
        
        if mode == "0":
            print("削除をキャンセルしました")
            return
        elif mode == "a":
            self._delete_multiple_backups(backups)
        elif mode == "s":
            self._delete_single_backup(backups)
        else:
            print("無効な選択です")
    
    def _delete_single_backup(self, backups):
        """単体バックアップの削除"""
        # ユーザーに選択させる
        while True:
            try:
                choice = input(f"\n削除するバックアップ番号を入力してください (1-{len(backups)}, 0でキャンセル): ").strip()
                if choice == "0":
                    print("削除をキャンセルしました")
                    return
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(backups):
                    selected_backup = backups[choice_num - 1]
                    break
                else:
                    print(f"1から{len(backups)}の間で入力してください")
            except ValueError:
                print("数値を入力してください")
        
        # 最終確認
        print(f"\n'{selected_backup['name']}' を削除します")
        confirm = input("この操作は取り消せません。続行しますか？ (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("削除をキャンセルしました")
            return
        
        # 削除実行
        try:
            shutil.rmtree(selected_backup['path'])
            print(f"削除完了: {selected_backup['name']}")
        except OSError as e:
            print(f"削除エラー: {e}")
    
    def _delete_multiple_backups(self, backups):
        """複数バックアップの削除"""
        print("\n削除したいバックアップの番号を入力してください")
        print("例: 1,3,5 または 1-3,5 または all")
        
        selection = input("選択: ").strip().lower()
        
        if selection == "all":
            # 全削除の確認
            print(f"\n全ての{len(backups)}個のバックアップを削除します")
            confirm = input("この操作は取り消せません。続行しますか？ (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("削除をキャンセルしました")
                return
            
            # 全削除実行
            deleted_count = 0
            for backup in backups:
                try:
                    shutil.rmtree(backup['path'])
                    print(f"削除: {backup['name']}")
                    deleted_count += 1
                except OSError as e:
                    print(f"削除エラー ({backup['name']}): {e}")
            
            print(f"削除完了: {deleted_count}個のバックアップを削除しました")
            return
        
        # 個別選択の解析
        selected_indices = self._parse_selection(selection, len(backups))
        if not selected_indices:
            print("無効な選択です")
            return
        
        # 選択されたバックアップを表示
        print("\n削除対象:")
        selected_backups = [backups[i] for i in selected_indices]
        for backup in selected_backups:
            print(f"  - {backup['name']}")
        
        # 最終確認
        confirm = input(f"\n{len(selected_backups)}個のバックアップを削除します。続行しますか？ (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("削除をキャンセルしました")
            return
        
        # 削除実行
        deleted_count = 0
        for backup in selected_backups:
            try:
                shutil.rmtree(backup['path'])
                print(f"削除: {backup['name']}")
                deleted_count += 1
            except OSError as e:
                print(f"削除エラー ({backup['name']}): {e}")
        
        print(f"削除完了: {deleted_count}個のバックアップを削除しました")
    
    def _parse_selection(self, selection, max_num):
        """選択文字列を解析してインデックスリストを返す"""
        indices = set()
        
        try:
            # カンマで分割
            parts = selection.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 範囲指定 (例: 1-3)
                    start, end = part.split('-', 1)
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1
                    if 0 <= start_idx < max_num and 0 <= end_idx < max_num and start_idx <= end_idx:
                        indices.update(range(start_idx, end_idx + 1))
                else:
                    # 単一指定
                    idx = int(part) - 1
                    if 0 <= idx < max_num:
                        indices.add(idx)
        except ValueError:
            return []
        
        return sorted(list(indices))
    
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
        print("現在のセーブディレクトリをクリアしています...")
        self.clear_directory(self.current_save_dir)
        print("クリア完了")
        
        # セーブファイルをコピー
        print(f"\nセーブファイルを {game_path} からコピーしています...")
        copied = self.copy_save_files(game_path, self.current_save_dir, "")
        if copied == 0:
            print("セーブファイルのコピーに失敗しました")
            return False
        
        print(f"{copied} ファイルをコピーしました")
        
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
        """メインメニューの表示と操作"""
        # 設定の確認
        config = self.load_config()
        if not config.get('initialized', False):
            print("まず初期化を行ってください:")
            print("python save-manager.py --init")
            return
        
        while True:
            # メニュー表示
            print("\n" + "="*50)
            print("UNDERTALE セーブデータ管理ツール")
            print(f"ゲームパス: {config.get('game_path', '未設定')}")
            print("="*50)
            
            # セーブ一覧を自動表示
            self.display_save_list()
            
            # メニュー選択肢
            print("\n=== メニュー ===")
            print("1. 💾 バックアップを作成")
            print("2. 🔄 バックアップから復元")
            print("3. 📁 セーブ一覧を表示")
            print("4. 🗑️  バックアップを削除")
            print("0. 終了")
            
            # ユーザー入力
            try:
                choice = input("\n選択してください [0-4]: ").strip()
            except KeyboardInterrupt:
                print("\n\n終了します")
                break
            
            # 選択に応じた処理
            if choice == "0":
                print("終了します")
                break
            elif choice == "1":
                self.create_backup()
            elif choice == "2":
                self.restore_backup()
            elif choice == "3":
                # 既に自動表示されているので、何もしない（次のループで再表示）
                continue
            elif choice == "4":
                self.delete_backup()
            else:
                print("無効な選択です。0-4で入力してください")

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