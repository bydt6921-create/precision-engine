from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
import threading
import os
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dex import DEX

class PrecisionEngineMobile(BoxLayout):
    def __init__(self, **kwargs):
        super(PrecisionEngineMobile, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        self.title_label = Label(text="PRECISION ENGINE (DEEP SCAN)", color=(1, 0.6, 0, 1), font_size='20sp', size_hint_y=None, height=40)
        self.add_widget(self.title_label)

        self.select_btn = Button(text="+ اضغط لاختيار ملف APK للفحص", background_color=(0.2, 0.2, 0.2, 1), color=(1, 1, 1, 1), font_size='15sp', size_hint_y=None, height=50)
        self.select_btn.bind(on_press=self.open_file_chooser)
        self.add_widget(self.select_btn)

        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=30)
        self.add_widget(self.progress_bar)

        self.result_box = TextInput(text="[وصف] بانتظار اختيار ملف APK لبدء الفحص العميق للكلاسات والميثودات...", background_color=(0.1, 0.1, 0.1, 1), foreground_color=(0, 1, 0, 1), readonly=True, font_size='12sp')
        self.add_widget(self.result_box)

    def open_file_chooser(self, instance):
        self.clear_widgets()
        self.filechooser = FileChooserIconView(filters=['*.apk'], path='/sdcard/')
        self.filechooser.bind(on_submit=self.on_file_selected)
        self.add_widget(self.filechooser)

    def on_file_selected(self, filechooser, selection, touch):
        if selection:
            file_path = selection[0]
            self.clear_widgets()
            self.__init__()
            self.result_box.text = f"[+] تم اختيار الملف:\n{os.path.basename(file_path)}\n\n[وصف] جاري فك حزمة الـ APK وقراءة الكلاسات..."
            threading.Thread(target=self.run_real_deep_analysis, args=(file_path,)).start()

    def run_real_deep_analysis(self, apk_path):
        try:
            app = APK(apk_path)
            dex_files = [DEX(app.get_dex(i)) for i in range(app.get_nb_dex())]
            total_dex = len(dex_files)
            Clock.schedule_once(lambda dt: self.update_log(f"[+] تم استخراج {total_dex} ملفات DEX. جاري فحص الكلاسات..."), 0)
            priority_keywords = ["billing", "purchase", "subscription", "license", "isVip", "isPro", "pay"]
            found_targets = []
            all_classes_count = sum(len(dex.get_classes()) for dex in dex_files)
            processed_classes = 0
            for dex_idx, dex in enumerate(dex_files):
                for clazz in dex.get_classes():
                    processed_classes += 1
                    class_name = clazz.get_name()
                    for method in clazz.get_methods():
                        method_name = method.get_name()
                        if any(kw in f"{class_name} {method_name}".lower() for kw in priority_keywords):
                            found_targets.append({"dex": f"classes{dex_idx+1}.dex", "class": class_name, "method": method_name})
                    if all_classes_count > 0:
                        progress_val = int((processed_classes / all_classes_count) * 100)
                        Clock.schedule_once(lambda dt, p=progress_val, cur=processed_classes, tot=all_classes_count: self.update_progress(p, cur, tot), 0)
            Clock.schedule_once(lambda dt: self.show_final_results(found_targets), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)), 0)

    def update_log(self, text):
        self.result_box.text += f"\n{text}"

    def update_progress(self, val, current, total):
        self.progress_bar.value = val
        self.result_box.text = f"[*] جاري فحص الكلاسات: {current} / {total} ({val}%)..."

    def show_final_results(self, targets):
        self.progress_bar.value = 100
        output = f"\n[✔] اكتمل التحليل العميق بنجاح!\n[!] الأهداف المطابقة: {len(targets)}\n\n"
        for idx, t in enumerate(targets[:20], 1):
            output += f"[{idx}] الكلاس: {t['class']}\n    - الميثود: {t['method']}\n--------------------\n"
        self.result_box.text = output

    def show_error(self, err_msg):
        self.result_box.text = f"\n[خطأ]: {err_msg}"

class PrecisionApp(App):
    def build(self):
        self.title = "Precision Engine - Mobile"
        return PrecisionEngineMobile()

if __name__ == '__main__':
    PrecisionApp().run() 
