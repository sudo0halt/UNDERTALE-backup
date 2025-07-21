# UNDERTALE セーブデータ管理ツール

## 使い方

1. このリポジトリをクローン
```bash
git clone https://github.com/sudo0halt/UNDERTALE-backup.git
cd UNDERTALE-backup
```

2. 自分の環境用に初期化
```bash
python save-manager.py --init
```

3. ツールを使用
```bash
python save-manager.py
```

## 構造
- `saves/current/` - アクティブなセーブファイル
- `saves/backups/` - 追加のセーブスロット
