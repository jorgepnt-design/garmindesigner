import Toybox.Test;

class TouchTestFace {
 var weatherPanel=false;var displayWidth=448;var displayHeight=486;var touchPoint="";var noticeText="";
 function initialize() {}
 function showWeather() { weatherPanel=true; }
 function showNotice(value) { noticeText=value; }
 function closeWeather() { weatherPanel=false; }
}
class TouchTestEvent {
 var x;var y;
 function initialize(px,py) { x=px;y=py; }
 function getCoordinates() { return [x,y]; }
}
class WeatherTestDc {
 var texts=[];
 function initialize() {}
 function getWidth() { return 448; }
 function getHeight() { return 486; }
 function setColor(fg,bg) {}
 function clear() {}
 function drawLine(x1,y1,x2,y2) {}
 function fillRectangle(x,y,w,h) {}
 function drawBitmap(x,y,image) {}
 function drawText(x,y,font,text,justify) { texts.add(text); }
 function contains(text) {
  for(var i=0;i<texts.size();i+=1) { if(texts[i].equals(text)) { return true; } }
  return false;
 }
}

(:test)
function stringComparisonRequiresValueEquality(logger) {
 var literal="weather";var allocated="xweather".substring(1,8);
 Test.assert(literal!=allocated);
 Test.assert(literal.equals(allocated));
 return true;
}
(:test)
function weatherSymbolValueAndLabelOpenWeather(logger) {
 var points=[[82,352],[80,404],[80,441]];
 for(var i=0;i<points.size();i+=1) {
  var face=new TouchTestFace();var delegate=new CustomDelegate(face);
  Test.assert(delegate.onPress(new TouchTestEvent(points[i][0],points[i][1])));
  Test.assert(face.weatherPanel);
 }
 return true;
}
(:test)
function allocatedWeatherTargetOpensWeather(logger) {
 var face=new TouchTestFace();var delegate=new CustomDelegate(face);
 Test.assert(delegate.open("xweather".substring(1,8)));
 Test.assert(face.weatherPanel);
 return true;
}
(:test)
function clockCoordinatesRemainUnlinked(logger) {
 var face=new TouchTestFace();var delegate=new CustomDelegate(face);
 Test.assert(delegate.onPress(new TouchTestEvent(239,257)));
 Test.assert(!face.weatherPanel);
 Test.assert(face.noticeText.find("Frei 239/257")!=null);
 return true;
}
(:test)
function alarmsShowMenuGuidance(logger) {
 var face=new TouchTestFace();var delegate=new CustomDelegate(face);
 Test.assert(delegate.onPress(new TouchTestEvent(380,441)));
 Test.assert(face.noticeText.equals("Alarme im Garmin-Uhrenmenue einstellen"));
 return true;
}
(:test)
function realWeatherViewSurvivesSleepAndRenders(logger) {
 var face=new CustomFace();
 face.onEnterSleep();face.showWeather();face.onEnterSleep();
 Test.assert(face.weatherPanel);
 face.onExitSleep();
 var dc=new WeatherTestDc();face.onUpdate(dc);
 Test.assert(face.weatherPanel);
 Test.assert(dc.contains("WETTER"));
 Test.assert(dc.contains("Oben halten: zurueck"));
 Test.assert(!face.noticeText.equals("P7: Wetterfehler"));
 face.closeWeather();
 Test.assert(!face.weatherPanel);
 return true;
}
