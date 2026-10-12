import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_enhanced_model():
    # 1. 加载新版数据
    print("📂 正在读取多维环境健康数据集...")
    df = pd.read_csv('health_training_data_v2.csv')

    # 2. 定义特征和标签
    # 现在我们有 6 个输入变量
    feature_cols = ['heart_rate', 'sleep_hours', 'steps', 'room_temp', 'humidity', 'co2_level']
    X = df[feature_cols]
    y = df['health_label']

    # 3. 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. 训练随机森林
    print("🧠 AI 正在学习生理与环境的关联规律...")
    model = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # 5. 验证模型
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"📊 模型训练完成！准确率: {acc:.2%}")
    print("\n[分类报告]")
    print(classification_report(y_test, y_pred))

    # 6. 持久化导出
    joblib.dump(model, 'health_model.pkl')
    print("💾 增强版 AI 模型已保存为 'health_model.pkl'")

if __name__ == "__main__":
    train_enhanced_model()