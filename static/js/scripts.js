// https://openweathermap.org/weather-conditions
var ICONS_MAP = {
    '01d': 'day.svg',
    '02d': 'cloudy-day-1.svg',
    '03d': 'cloudy-day-2.svg',
    '04d': 'cloudy-day-3.svg',
    '09d': 'rainy-6.svg',
    '10d': 'rainy-5.svg',
    '11d': 'thunder.svg',
    '13d': 'snowy-5.svg',
    '50d': 'cloudy.svg',
    '01n': 'night.svg',
    '02n': 'cloudy-night-1.svg',
    '03n': 'cloudy-night-2.svg',
    '04n': 'cloudy-night-3.svg',
    '09n': 'rainy-6.svg',
    '10n': 'rainy-5.svg',
    '11n': 'thunder.svg',
    '13n': 'snowy-5.svg',
    '50n': 'cloudy.svg',
}

var MONTHS_MAP = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря'
}

function getCookie(name) {
    var matches = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

function initWeatheBlock({root_el, title, icon, temp, wind}){
    root_el.querySelector('.ww_title').textContent = title
    root_el.querySelector('img').src = '/static/amcharts_weather_icons_1.0.0/animated/' + icon;
    root_el.querySelector('.ww_temp').setAttribute('class', 'ww_temp ' + (temp > 5 ? 'hot' : 'cold'));
    root_el.querySelector('.ww_temp span').textContent = parseInt(temp);
    root_el.querySelector('.ww_wind span').textContent = wind;
}

function get_random_action(){
    return 'ok';
}

function $(selector){
    function _({selector, root, one}) { 
        var root = root || document.body;
        if (one){
            return root.querySelector(selector);
        }
        return root.querySelectorAll(selector);
    }

    if (typeof(selector) == 'string') {
        var selector = {selector: selector};
    }
    return _(selector)
}


function get_next_days_weather() {
    const city_id = getCookie('city_id');
    const ow_api_token = getCookie('ow_api_token');

    fetch('http://api.openweathermap.org/data/2.5/forecast?units=metric&id=' + city_id + '&APPID=' + ow_api_token).then(
        function(response){
            return response.json();
    }).then(function(response){
        console.log(response);
        
        var response = response.list;

        var widget = $({selector: '.weather-widget', one: true})

        initWeatheBlock({
            root_el: widget,
            icon: ICONS_MAP[response[0].weather[0].icon],
            temp: response[0].main.temp,
            wind: response[0].wind.speed
        });

        var response = response.slice(1)

        var widget = $('.weather-widget .ww_next-hours .ww_block')
        widget.forEach(function(item, i, arr){
            initWeatheBlock({
                root_el: item,
                title: response[i].dt_txt.split(' ')[1].slice(0, 5),
                icon: ICONS_MAP[response[i].weather[0].icon],
                temp: response[i].main.temp,
                wind: response[i].wind.speed
            });
        });

        var hours = 36;
        const measure_step_hours = 3;

        var widget = $('.weather-widget .ww_next-days .ww_block')
        widget.forEach(function(item, i, arr){
            const dt = new Date(response[0].dt * 1000);
            const next_index = ((hours - dt.getHours()) / measure_step_hours) + 1;
            hours += 24;

            initWeatheBlock({
                root_el: item,
                title: dt.getDate() +  ' ' + MONTHS_MAP[dt.getMonth()],
                icon: ICONS_MAP[response[next_index].weather[0].icon],
                temp: response[next_index].main.temp,
                wind: response[next_index].wind.speed
            });

        });
    });
}

var weather_interval_id = setInterval(get_next_days_weather, 5 * 60 * 1000);

$({selector: '.weather-widget img.big', one: true}).addEventListener('load', function(event){
    $({selector: '.weather-widget', one: true}).style.right = 0;
});
get_next_days_weather();



var actions = {
    ['pavel']: function() {
        var h1 = $({selector: 'h1', one: true});
        h1.textContent = 'Моё почтение, создатель';
        setTimeout(function(){
            h1.textContent = '';
        }, 5 * 1000);
    }
}

var current_persons = [];
var absence_time_threshold = 1; // minute
var current_absence_time = {}; // person: time


var socket = new WebSocket("ws://localhost:5000/ws");

socket.onopen = function() {
  console.log("Соединение установлено.");
};

socket.onclose = function(event) {
  if (event.wasClean) {
    console.log('Соединение закрыто чисто');
  } else {
    console.log('Обрыв соединения');
  }
  console.log('Код: ' + event.code + ' причина: ' + event.reason);
};

socket.onmessage = function(event) {
    var data = JSON.parse(event.data)
    // if (current_persons != data) {
    //     var current_date = new Date()
    //     var c_ab_time = current_absence_time[data] || 0;
    //     var is_time = Math.abs((current_date.getTime() - c_ab_time) / 1000 / 60) > absence_time_threshold;
    //     if (is_time) {
    //         current_absence_time[data] = (new Date()).getTime();
    //         (actions[data] || get_random_action)();
    //         current_persons = data;
    //     }
    // }
};

socket.onerror = function(error) {
  console.log("Ошибка " + error.message);
};


// socket.send("start");