import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QScrollArea,
                             QSizePolicy, QDialog, QHBoxLayout, QLineEdit, QFormLayout, QDialogButtonBox, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt


class ImageProcessingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('圖像處理程式')
        self.image = None
        self.initUI()
        self.setGeometry(100, 100, 1200, 900)  # 放大視窗尺寸

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)  # 置中所有 UI 元素

        # 創建滾動視窗區域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # 顯示圖片的 QLabel
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)  # 置中顯示圖片
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(False)

        # 將 QLabel 添加到滾動區域中
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        # 載入圖片按鈕
        load_button = QPushButton('載入圖片', self)
        load_button.clicked.connect(self.load_image)
        layout.addWidget(load_button)

        # 灰階處理按鈕
        gray_button = QPushButton('轉換為灰階並比較差異', self)
        gray_button.clicked.connect(self.convert_to_grayscale_and_compare)
        layout.addWidget(gray_button)

        # 調整亮度與對比按鈕
        adjust_button = QPushButton('調整亮度與對比', self)
        adjust_button.clicked.connect(self.open_brightness_contrast_dialog)
        layout.addWidget(adjust_button)

        # 手動二值化按鈕
        thresh_button = QPushButton('手動二值化圖片', self)
        thresh_button.clicked.connect(self.manual_threshold)
        layout.addWidget(thresh_button)

        # 直方圖顯示按鈕
        hist_button = QPushButton('顯示灰階直方圖', self)
        hist_button.clicked.connect(self.show_histogram)
        layout.addWidget(hist_button)

        self.setLayout(layout)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '選擇圖片', '', 'Image files (*.jpg *.jpeg *.bmp)')
        if file_name:
            self.image = cv2.imread(file_name)
            if self.image is None:
                self.image_label.setText("無法載入圖片")
            else:
                self.display_image(self.image)

    def display_image(self, img):
        """ 將 OpenCV 圖片轉換為 QImage 並顯示，保持原始大小 """
        qformat = QImage.Format_RGB888 if len(img.shape) == 3 else QImage.Format_Grayscale8
        h, w = img.shape[:2]
        img = QImage(img.data, w, h, img.strides[0], qformat)
        img = img.rgbSwapped()  # OpenCV 使用 BGR，因此我們要轉換成 RGB

        # 將圖片轉換為 QPixmap 並顯示，保持圖片原尺寸
        pixmap = QPixmap.fromImage(img)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()  # 調整 QLabel 大小以適應圖片原始尺寸

    def convert_to_grayscale_and_compare(self):
        if self.image is not None:
            # 獲取圖像的高、寬以及 RGB 通道數
            h, w, _ = self.image.shape
            # 公式 A: GRAY = (R + G + B) / 3.0
            gray_avg = np.zeros((h, w), dtype=np.uint8)
            for i in range(h):
                for j in range(w):
                    B, G, R = self.image[i, j]
                    gray_avg[i, j] = (R + G + B) / 3

            # 公式 B: GRAY = 0.299*R + 0.587*G + 0.114*B
            gray_weighted = np.zeros((h, w), dtype=np.uint8)
            for i in range(h):
                for j in range(w):
                    B, G, R = self.image[i, j]
                    gray_weighted[i, j] = 0.299 * R + 0.587 * G + 0.114 * B

            # 顯示兩張灰階圖片到彈出視窗
            dialog = QDialog(self)
            dialog.setWindowTitle('灰階轉換結果')
            dialog.setGeometry(100, 100, 1000, 600)

            layout = QHBoxLayout()

            # 將公式 A 的灰階圖像顯示
            gray_avg_label = QLabel(dialog)
            pixmap_avg = self.convert_cv_to_pixmap(gray_avg)
            gray_avg_label.setPixmap(pixmap_avg)
            gray_avg_label.adjustSize()  # 確保 QLabel 大小適應圖片
            layout.addWidget(gray_avg_label)

            # 將公式 B 的灰階圖像顯示
            gray_weighted_label = QLabel(dialog)
            pixmap_weighted = self.convert_cv_to_pixmap(gray_weighted)
            gray_weighted_label.setPixmap(pixmap_weighted)
            gray_weighted_label.adjustSize()  # 確保 QLabel 大小適應圖片
            layout.addWidget(gray_weighted_label)

            dialog.setLayout(layout)
            dialog.exec_()

            # 比較兩張灰階圖像的差異，並顯示到主視窗
            difference = cv2.absdiff(gray_avg, gray_weighted)
            self.display_image(difference)

    def convert_cv_to_pixmap(self, cv_img):
        """ 將 OpenCV 圖像轉換為 QPixmap """
        qformat = QImage.Format_RGB888 if len(cv_img.shape) == 3 else QImage.Format_Grayscale8
        h, w = cv_img.shape[:2]
        img = QImage(cv_img.data, w, h, cv_img.strides[0], qformat)
        if len(cv_img.shape) == 3:  # 如果是彩色圖像，進行 RGB 轉換
            img = img.rgbSwapped()
        pixmap = QPixmap.fromImage(img)
        return pixmap

    def open_brightness_contrast_dialog(self):
        if self.image is not None:
            dialog = BrightnessContrastDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                brightness, contrast = dialog.get_values()
                self.adjust_brightness_contrast(brightness, contrast)

    def adjust_brightness_contrast(self, brightness, contrast):
        if self.image is not None:
            adjusted_img = cv2.convertScaleAbs(self.image, alpha=contrast, beta=brightness)
            self.display_image(adjusted_img)

    def manual_threshold(self):
        if self.image is not None:
            gray_img = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            _, binary_img = cv2.threshold(gray_img, 128, 255, cv2.THRESH_BINARY)
            self.display_image(binary_img)

    def show_histogram(self):
        if self.image is not None:
            gray_img = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray_img], [0], None, [256], [0, 256])
            plt.plot(hist)
            plt.title('Gray Scale Histogram')
            plt.show()


class BrightnessContrastDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('調整亮度與對比')
        self.brightness_input = QLineEdit(self)
        self.contrast_input = QLineEdit(self)

        # 設置範圍提示
        self.brightness_input.setPlaceholderText('亮度: -100 至 100')
        self.contrast_input.setPlaceholderText('對比: 0.0 至 3.0')

        form_layout = QFormLayout()
        form_layout.addRow('亮度:', self.brightness_input)
        form_layout.addRow('對比:', self.contrast_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_values(self):
        try:
            brightness = int(self.brightness_input.text())
            contrast = float(self.contrast_input.text())

            # 檢查範圍
            if not (-100 <= brightness <= 100):
                raise ValueError("亮度必須在 -100 至 100 之間")
            if not (0.0 <= contrast <= 3.0):
                raise ValueError("對比必須在 0.0 至 3.0 之間")
            return brightness, contrast
        except ValueError as e:
            QMessageBox.warning(self, '輸入錯誤', str(e))
            return None, None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageProcessingApp()
    window.show()
    sys.exit(app.exec_())