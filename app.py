from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)

# Load mô hình Random Forest đã lưu
model = joblib.load("random_forest.pkl")

# Danh sách nhãn theo đúng thứ tự bạn yêu cầu
pollution_labels = ["Trung Bình", "Tốt", "Xấu"]


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json

        # Xác định các thuộc tính đầu vào cần thiết
        required_features = ["CO(GT)", "NO2(GT)", "NOx(GT)", "C6H6(GT)"]

        # Kiểm tra nếu thiếu bất kỳ thông tin đầu vào nào
        if not all(feature in data for feature in required_features):
            return jsonify({'error': 'Thiếu thông tin đầu vào'}), 400

        # Lấy dữ liệu theo đúng thứ tự mô hình
        features = [data[feature] for feature in required_features]

        # Dự đoán bằng mô hình
        prediction = model.predict([features])[0]

        # Chuyển đổi dự đoán từ số (0,1,2) thành nhãn đúng thứ tự
        pollution_level = pollution_labels[prediction]

        return jsonify({'prediction': pollution_level})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
