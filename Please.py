from funcs import (
    MergeSort, Merge, SelectionSort, InsertionSort, BubbleSort, 
    QuickSort, CountingSort, partition, BucketSort, RadixSort, 
    counting_sort_for_radix
)
import time
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from PyQt5 import uic
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


##################### Background Scraper Thread ######################
class ScraperThread(QThread):
    data_ready = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._stop = False
        self._pause = False
        self.mutex = QMutex()
        self.condition = QWaitCondition()

    def pause(self):
        self.mutex.lock()
        self._pause = True
        self.mutex.unlock()

    def resume(self):
        self.mutex.lock()
        self._pause = False
        self.condition.wakeAll()
        self.mutex.unlock()

    def stop(self):
        self.mutex.lock()
        self._stop = True
        self.condition.wakeAll()
        self.mutex.unlock()

    def run(self):
        driver = None
        try:
            chrome_options = Options()
            # Headless removed so the Chrome window is visible
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=chrome_options)
    
            data = []
            base_url = self.url + "?page={}"
            total_pages = 2500 
            total_expected = 25000
            scraped = 0
                
            for page in range(1, total_pages + 1):
                self.mutex.lock()
                if self._stop:
                    self.mutex.unlock()
                    break
                if self._pause:
                    self.condition.wait(self.mutex)
                self.mutex.unlock()

                driver.get(base_url.format(page))
    
                last_height = driver.execute_script("return document.body.scrollHeight")
                for _ in range(5):
                    self.mutex.lock()
                    if self._stop:
                        self.mutex.unlock()
                        break
                    self.mutex.unlock()

                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                self.mutex.lock()
                if self._stop:
                    self.mutex.unlock()
                    break
                self.mutex.unlock()
    
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-blk"))
                    )
                except:
                    print(f"No books found on page {page}")
                    continue
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                books = soup.select("div.product-blk")
    
                for b in books:
                    self.mutex.lock()
                    if self._stop:
                        self.mutex.unlock()
                        break
                    self.mutex.unlock()

                    title_elem = b.select_one(".product-title")
                    if title_elem:
                        title = title_elem.get_text(strip=True) 
                    else: 
                        continue  
    
                    pack = b.select_one(".product-pack")
                    pack = pack.get_text(strip=True) if pack else ""
    
                    author = b.select_one(".author a")
                    author = author.get_text(strip=True) if author else ""
    
                    stock = b.select_one(".product-stock")
                    stock = stock.get_text(strip=True) if stock else ""
    
                    list_price = b.select_one(".product-price.list_price")
                    list_price = list_price.get_text(strip=True) if list_price else ""
    
                    sale_price = b.select_one(".product-price .sale-price")
                    sale_price = sale_price.get_text(strip=True) if sale_price else ""
                    
                    discount = b.select_one(".discounts span")
                    discount = discount.get_text(strip=True) if discount else ""
    
                    save_upto = b.select_one(".save-upto")
                    save_upto = save_upto.get_text(strip=True) if save_upto else ""
                    
                    data.append([
                        title, author, pack, stock,
                        list_price, sale_price, discount, save_upto
                    ])
                    scraped += 1
    
                if self._stop:
                    break

                progress = int((scraped / total_expected) * 100)
                self.progress.emit(min(progress, 100))
    
                if scraped >= total_expected:
                    break
    
            if driver:
                driver.quit()
            
            print(f"Scraping stopped/complete — {len(data)} items collected.")
            self.data_ready.emit(data)
            self.progress.emit(100)
    
        except Exception as e:
            if driver:
                driver.quit()
            self.error.emit(str(e))


##################### Main Window #############################
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Scraper.ui", self)

        self.Button.clicked.connect(self.start_scraping)
        self.table.horizontalHeader().sectionClicked.connect(self.header_clicked)
        self.btnPause.clicked.connect(self.pause_scraping)
        self.btnResume.clicked.connect(self.resume_scraping)
        self.btnStop.clicked.connect(self.stop_scraping)
        self.btnSearch.clicked.connect(self.search_by_title)

    def start_scraping(self):
        url = self.tbox.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return

        self.Button.setEnabled(False)
        self.Button.setText("Scraping...")
        self.table.setRowCount(0)
        self.pBar.setValue(0)
        self.status_label.setText("Status: Running")

        self.thread = ScraperThread(url)
        self.thread.data_ready.connect(self.load_table)
        self.thread.error.connect(self.show_error)
        self.thread.finished.connect(self.scraping_done)
        self.thread.progress.connect(self.update_progress)
        self.thread.start()

    def update_progress(self, value):
        self.pBar.setValue(value)

    def load_table(self, data):
        headers = [
            "Title", "Author", "Format/Year", "Stock",
            "List Price", "Price", "Discount", "Save Upto"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(data))
    
        for r_idx, row in enumerate(data):
            for c_idx, val in enumerate(row):
                self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def search_by_title(self):
        query = self.search_input.text().strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                title_text = item.text().lower()
                if query in title_text or not query:
                    self.table.setRowHidden(row, False)
                else:
                    self.table.setRowHidden(row, True)

    def show_error(self, message):
        QMessageBox.critical(self, "Scraping Error", message)
        self.pBar.setValue(0)
        self.status_label.setText("Status: Error")
        self.scraping_done()

    def scraping_done(self):
        self.Button.setEnabled(True)
        self.Button.setText("Scrape")

    def pause_scraping(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.pause()
            self.status_label.setText("Status: Paused")

    def resume_scraping(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.resume()
            self.status_label.setText("Status: Running")

    def stop_scraping(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.status_label.setText("Status: Stopped")
            self.scraping_done()

    def header_clicked(self, column_index):
        algo = self.comboBox.currentText().strip()
        print(f"Selected Sorting Algorithm: {algo}")

        data = [] 
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        if not data:
            return

        if hasattr(self, "last_sort_col") and self.last_sort_col == column_index:
            self.sort_reverse = not getattr(self, "sort_reverse", False)
        else:
            self.sort_reverse = False
        self.last_sort_col = column_index

        start_time = time.time()

        if algo == "Merge":
            MergeSort(data, 0, len(data) - 1, column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Selection":
            SelectionSort(data, 0, len(data), column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Bubble":
            BubbleSort(data, 0, len(data), column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Insertion":
            InsertionSort(data, 0, len(data), column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Quick":
            QuickSort(data, 0, len(data) - 1, column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Counting":
            CountingSort(data, column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Radix":
            RadixSort(data, column_index=column_index, reverse=self.sort_reverse)
        elif algo == "Bucket":
            BucketSort(data, column_index=column_index, reverse=self.sort_reverse)
    
        end_time = time.time()
        runtime_ms = (end_time - start_time) * 1000

        self.time_label.setText(f"{runtime_ms:.2f}")
        self.load_table(data)
        

# ----------------- Main -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())