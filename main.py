#!/usr/bin/python3
# в QTDesigner создаем clock.ui
# pyuic5 clock.ui -o clock.py

import sys, json
from datetime import datetime
import paho.mqtt.client as mqtt

from PyQt5 import QtWidgets, QtCore

import clock  # Это наш конвертированный файл дизайна

DAYS = (
    "Поедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
)

class ExampleApp(QtWidgets.QMainWindow, clock.Ui_MainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000)

        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.connect('10.0.0.10', 1883, 60)
        self.mqttc.subscribe("house/wether")
        self.mqttc.loop_start()


    def on_timer(self):
        t = datetime.now()
        self.lcdHour.display(t.hour)
        self.lcdMinute.display(t.minute)
        self.lcdSecond.display(t.second)
        self.lblDate.setText('%s / %s' %(t.day, t.month))
        day = t.weekday()
        self.lblWeekday.setText(DAYS[day])

        palette = self.lblWeekday.palette()
        color = QtCore.Qt.red if day in (5,6) else QtCore.Qt.black

        palette.setColor(self.label.foregroundRole(), color)
        self.lblWeekday.setPalette(palette)



    def on_message(self, mqttc, obj, msg):
        msg = json.loads(msg.payload.decode("ascii"))
        data = msg['Data']
        self.lcdPressure.display(data['Pressure'])
        self.lcdHumidity.display(data['mmHgExt'])
        self.lcdExtTemp.display(data['TempExt'])
        self.lcdHomeTemp.display(data['Temp']-3)


    def on_connect(self, *args):
        #print("on_connect", args)
        pass


    def on_disconnect(self, *args):
        #print("on_disconnect", args)
        pass



def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()