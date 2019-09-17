#!/usr/bin/python3
# в QTDesigner создаем clock.ui
# pyuic5 clock.ui -o clock.py

import sys, json, requests
from datetime import datetime
import paho.mqtt.client as mqtt
from PyQt5 import QtWidgets, QtCore, QtGui
import clock

clPRESSURE = '#B8860B'
clHUMIDITY = '#0000FF'
clTEMPEXT  = '#FF7F50'
clTEMP     = '#008000'

DAYS = (
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
)

Hist = []

class ExampleApp(QtWidgets.QMainWindow, clock.Ui_MainWindow):

    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле clock.py
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.courses = None
        self.wait_data=False

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000)

        self.mqttc = mqtt.Client()
        self.mqttc.on_message = self.on_message
        self.mqttc.connect('10.0.0.10', 1883, 60)
        self.mqttc.subscribe("house/wether")
        self.mqttc.loop_start()

        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.Pressure,  self.Humidity,  self.ExtTemp, self.HomeTemp = (None,)*4

        self.set_color(self.label,   clPRESSURE)
        self.set_color(self.label_2, clHUMIDITY)
        self.set_color(self.label_4, clTEMPEXT)
        self.set_color(self.label_5, clTEMP)


    def set_color(self, item, color = 'black'):
        if color.startswith('#'):
            color = QtGui.QColor(int(color[1:3],16), int(color[3:5],16), int(color[5:],16))
        else:
            color = getattr(QtCore.Qt, color)
        palette = item.palette()
        palette.setColor(item.foregroundRole(), color)
        item.setPalette(palette)

    def on_timer(self):
        t = datetime.now()
        self.lcdHour.display(t.hour)
        self.lcdMinute.display(t.minute)
        self.lcdSecond.display(t.second)
        self.lblDate.setText('%s / %s' %(t.day, t.month))
        day = t.weekday()
        self.lblWeekday.setText(DAYS[day])

        color = 'darkGreen' if day==4 else ( 'red' if day in (5,6) else 'black' )
        self.set_color(self.lblWeekday,color)

        if (t.second == 0 and t.minute==0)or(self.wait_data and not(self.Pressure is None)):
            if self.Pressure is None:
                self.wait_data = True
            else:
                if len(Hist) == 24: del Hist[0]
                Hist.append( {
                 'Pressure': self.Pressure,
                 'mmHg':     self.Humidity,
                 'TempExt':  self.ExtTemp,
                 'Temp':     self.HomeTemp
                })
                self.wait_data = False

        self.check_course(t)
        self.draw_graphic()


    def on_message(self, mqttc, obj, msg):
        msg = json.loads(msg.payload.decode("ascii"))
        data = msg['Data']

        self.Pressure = data['Pressure']
        self.Humidity = data['mmHgExt']
        self.ExtTemp  = data['TempExt']
        self.HomeTemp = data['Temp']-3

        self.lcdPressure.display(self.Pressure)
        self.lcdHumidity.display(self.Humidity)
        self.lcdExtTemp.display(self.ExtTemp)
        self.lcdHomeTemp.display(self.HomeTemp)

        if len(Hist)<(datetime.now().hour + 1):
            # заполним график до текущего часа
            for x in range(datetime.now().hour+1):
                Hist.append( {
                 'Pressure': self.Pressure,
                 'mmHg':     self.Humidity,
                 'TempExt':  self.ExtTemp,
                 'Temp':     self.HomeTemp
                })


    def check_course(self, time):
        if not self.courses is None:
            if time.hour<11 or time.minute<35 or self.courses['day'] == time.day : return
        crs = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        if crs.status_code!=200: return
        crs = json.loads(crs.text)
        time = crs['Date'][8:10]

        if self.courses is None:
            self.courses = {'day':int(time)}

        val = crs['Valute']['EUR']
        txt = ' ' if val['Previous'] == val['Value'] else ('+' if val['Previous']< val['Value'] else '-')
        self.lblEUR.setText('%s %s' % (val['CharCode'], txt))
        self.lcdEUR.display(val['Value'])

        val = crs['Valute']['USD']
        txt = ' ' if val['Previous'] == val['Value'] else ('+' if val['Previous']< val['Value'] else '-')
        self.lblUSD.setText('%s %s' % (val['CharCode'], txt))
        self.lcdUSD.display(val['Value'])

    def Line(self, x1, y1, x2, y2, color='black'):
        p1 = QtCore.QPointF(x1, y1)
        p2 = QtCore.QPointF(x2, y2)
        if color.startswith('#'):
            color = QtGui.QColor(int(color[1:3], 16), int(color[3:5], 16), int(color[5:], 16))
        else:
            color = getattr(QtCore.Qt, color)
        self.scene.addLine(QtCore.QLineF(p1, p2),color)

    def draw_graphic(self):
        self.scene.clear()
        pen = QtGui.QPen(QtCore.Qt.green)

        for i in range(12):
            for j in range(8):
                r = QtCore.QRectF(QtCore.QPointF(i * 20, j * 20), QtCore.QSizeF(20, 20))
                self.scene.addRect(r, pen)
        # {
        #  'Pressure': 700, # В Москве  709 мм.рт.ст. – отмечено 25 ноября 1973 года,  самое высокое – 782 мм.рт.ст. – 14 декабря 1944 года.
        #  'mmHg': 76, # среняя 76%
        #  'TempExt':0,
        #  'Temp': 0
        # },
        x = -10
        self.Line(0, 80, 240, 80, '#808080')
        for n in Hist:
            pr = 160 - (n['Pressure'] - 710)
            hm = 160 - int((160/100) * n['mmHg'])
            et = 80 - n['TempExt'] * 2
            t =  80 - n['Temp'] * 2

            if x==-10:
                pass
            else:
                self.Line(x,et0, x + 10, et,clTEMPEXT)
                self.Line(x, t0, x + 10,  t, clTEMP)
                self.Line(x,pr0, x + 10, pr, clPRESSURE)
                self.Line(x,hm0, x + 10, hm, clHUMIDITY)
            x += 10
            et0, t0, pr0, hm0 = et, t, pr, hm


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':
    main()
