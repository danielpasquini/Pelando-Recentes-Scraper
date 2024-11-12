import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QProgressBar, QLabel
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtCore import QUrl, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from datetime import datetime, timedelta
import time
import re
import math

class ScraperThread(QThread):
    progress_update = pyqtSignal(int)
    finished_scraping = pyqtSignal(list)
    stop_requested = False

    def __init__(self, num_promotions, min_upvotes, parse_time_func):
        super().__init__()
        self.num_promotions = num_promotions
        self.min_upvotes = min_upvotes
        self.parse_relative_time = parse_time_func
        self.num_scrolls = math.ceil(num_promotions / 32)

    def run(self):
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument("--headless")
        service = Service(os.path.join(os.path.dirname(__file__), 'geckodriver'))
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.get("https://www.pelando.com.br/recentes")

        promotions = []
        seen_titles = set()
        scroll_pause_time = 0.1  

        for scroll in range(self.num_scrolls):
            if self.stop_requested:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            if (scroll + 1) % 3 == 0 or scroll == self.num_scrolls - 1:
                self.progress_update.emit(scroll + 1)

            items = driver.find_elements(By.CSS_SELECTOR, "li.sc-4af6a208-2")
            for item in items:
                title = link = None
                try:
                    title_element = item.find_element(By.CSS_SELECTOR, "a.sc-kjKYmT")
                    title = title_element.text.strip()
                    link = title_element.get_attribute("href")
                except:
                    title = "No title found"
                    link = "No link found"

                upvotes = 0
                try:
                    upvote_text = item.find_element(By.CSS_SELECTOR, "span.sc-guhxjM").text.strip()
                    upvotes = int(upvote_text.replace("º", ""))
                except:
                    upvotes = 0

                upload_time = growth_rate = 0
                try:
                    time_text = item.find_element(By.CSS_SELECTOR, "span.sc-egpspN.Npowk").text.strip()
                    upload_time = self.parse_relative_time(time_text)
                    if upload_time:
                        time_difference = (datetime.now() - upload_time).total_seconds() / 60
                        growth_rate = upvotes / time_difference if time_difference > 0 else 0
                    upload_time = upload_time.strftime('%Y-%m-%d %H:%M:%S') if upload_time else "Unknown"
                except:
                    upload_time = "No upload time found"

                if title and title not in seen_titles and upvotes >= self.min_upvotes:
                    promotions.append({
                        "title": title,
                        "upvotes": upvotes,
                        "upload_time": upload_time,
                        "growth_rate": growth_rate,
                        "link": link
                    })
                    seen_titles.add(title)

                if len(promotions) >= self.num_promotions:
                    self.finished_scraping.emit(sorted(promotions, key=lambda x: x['growth_rate'], reverse=True))
                    driver.quit()
                    return

        driver.quit()
        self.finished_scraping.emit(sorted(promotions, key=lambda x: x['growth_rate'], reverse=True))

    def stop(self):
        self.stop_requested = True

class PromotionScraperApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pelando Promotion Scraper")
        self.setGeometry(100, 100, 800, 650)

        icon_path = os.path.join(os.path.dirname(__file__), 'pelando.ico')
        self.setWindowIcon(QIcon(icon_path))

        font = QtGui.QFont("Arial", 11)
        self.setFont(font)

        self.setStyleSheet("""
            QWidget {
                background-color: #1C1C1C;
                color: #FFFFFF;
                font-family: 'Arial';
            }
            QLabel {
                font-size: 14px;
                color: #FFA07A;
                font-weight: bold;
            }
            QLineEdit, QPushButton, QTableWidget, QProgressBar {
                border-radius: 8px;
                padding: 8px;
                font-family: 'Arial';
            }
            QLineEdit {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #444444;
            }
            QPushButton {
                background-color: #FFA07A;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB07B;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QProgressBar {
                background-color: #333333;
                border: none;
                border-radius: 10px;
                height: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFA07A, stop:1 #FFB07B
                );
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #292929;
                color: #FFFFFF;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #333333;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #666666;
                border-radius: 5px;
            }
            QTableWidget {
                color: #FFFFFF;
                background-color: #1C1C1C;
                selection-background-color: #444444;
                selection-color: #FFFFFF;
            }
            QTableWidget::corner-button {
                background-color: #1C1C1C;
                border: none;
            }
            QTableWidget QHeaderView::section {
                background-color: #292929;
            }
            QLabel[link=true] {
                color: #FFFFFF;
                text-decoration: none;
            }
            QLabel[link=true] a {
                color: #FFFFFF;
                text-decoration: none;
            }
            QLabel[link=true] a:hover {
                color: #FFA07A;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #292929;
                border: none;
            }
        """)

        self.num_promotions_label = QtWidgets.QLabel("Number of promotions to scrape:", self)
        self.num_promotions_input = QtWidgets.QLineEdit(self)
        self.num_promotions_input.setText("200")

        self.num_to_display_label = QtWidgets.QLabel("Number of top promotions to display:", self)
        self.num_to_display_input = QtWidgets.QLineEdit(self)
        self.num_to_display_input.setText("20")

        self.min_upvotes_label = QtWidgets.QLabel("Minimum upvotes to display:", self)
        self.min_upvotes_input = QtWidgets.QLineEdit(self)
        self.min_upvotes_input.setText("100")

        self.scrape_button = QtWidgets.QPushButton("Scrape Promotions", self)
        self.scrape_button.clicked.connect(self.start_scraping)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(10)
        self.progress_bar.setTextVisible(False)

        self.stop_button = QtWidgets.QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_scraping)
        self.stop_button.setEnabled(False)

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "Upvotes", "Upload Time", "Growth Rate"])
        self.table.setColumnWidth(0, 450)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 150)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.num_promotions_label)
        layout.addWidget(self.num_promotions_input)
        layout.addWidget(self.num_to_display_label)
        layout.addWidget(self.num_to_display_input)
        layout.addWidget(self.min_upvotes_label)
        layout.addWidget(self.min_upvotes_input)
        layout.addWidget(self.scrape_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.stop_button, alignment=QtCore.Qt.AlignRight)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def parse_relative_time(self, relative_time):
        now = datetime.now()
        time_mapping = {"seg": "seconds", "min": "minutes", "h": "hours", "d": "days"}
        match = re.search(r"(\d+)\s*(seg|min|h|d)", relative_time)
        if match:
            value, unit = match.groups()
            value = int(value)
            if unit in time_mapping:
                kwargs = {time_mapping[unit]: value}
                return now - timedelta(**kwargs)
        return None

    def start_scraping(self):
        try:
            num_promotions = int(self.num_promotions_input.text())
            min_upvotes = int(self.min_upvotes_input.text())
            self.progress_bar.setMaximum(math.ceil(num_promotions / 32))
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter valid integer values.")
            return

        self.scrape_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.scraper_thread = ScraperThread(num_promotions, min_upvotes, self.parse_relative_time)
        self.scraper_thread.progress_update.connect(self.progress_bar.setValue)
        self.scraper_thread.finished_scraping.connect(self.update_table)
        self.scraper_thread.start()

    def stop_scraping(self):
        self.scraper_thread.stop()
        self.scrape_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)

    def update_table(self, promotions):
        self.scrape_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.table.setRowCount(len(promotions))
        for row, promo in enumerate(promotions):
            title_label = QLabel(f'<a href="{promo["link"]}" style="color: white; text-decoration: none;">{promo["title"]}</a>')
            title_label.setOpenExternalLinks(True)
            title_label.setProperty("link", True)  # Use a custom property for styling

            self.table.setCellWidget(row, 0, title_label)
            self.table.setItem(row, 1, QTableWidgetItem(str(promo["upvotes"])))
            self.table.setItem(row, 2, QTableWidgetItem(promo["upload_time"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{promo['growth_rate']:.2f} upvotes/min"))

        for i in range(4):
            self.table.resizeColumnToContents(i)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = PromotionScraperApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()