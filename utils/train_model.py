import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_health_model():
    # 1. 加载数据
    print("📂 正在加载训练数据...")
    df = pd.read_csv('health_training_data.csv')

    # 2. 划分特征 (X) 和 标签 (y)
    # X 包含我们要喂给 AI 的指标，y 是我们要预测的健康等级
    X = df[['heart_rate', 'sleep_hours', 'steps']]
    y = df['health_label']

    # 3. 划分训练集和测试集
    # 80% 的数据用于训练，20% 用于验证 AI 学得好不好
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. 初始化随机森林分类器
    # n_estimators=100 表示使用 100 棵决策树投票决定结果
    print("🧠 AI 正在学习中...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)

    # 5. 训练模型
    model.fit(X_train, y_train)

    # 6. 模型评估
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ 模型训练完成！准确率为: {accuracy:.2%}")
    
    # 打印详细分类报告（可选）
    print("\n详细评估指标:")
    print(classification_report(y_test, y_pred))

    # 7. 模型持久化 (保存模型为文件)
    joblib.dump(model, 'health_model.pkl')
    print("💾 模型已保存为 'health_model.pkl'")

if __name__ == "__main__":
    train_health_model()