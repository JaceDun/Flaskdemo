$(function(){
    var dom = document.getElementById("container");
    var myChart = echarts.init(dom);
    option = null;
    var symbol = 'emptyCircle';
    var symbolSize = 10;
    var linedata = {
        'name':["car1","car2"],
       // 'data':[[[100,900],[300,900],[300,700],[100,700],[100,900]],
        //    [[800,500],[800,300],[800,200],[800,300],[500,300],[500,500],[800,500]]]
        'data':[[],[]]
    };
    var newseries = [];
    var series_template = {
                id: 'id1',
                type: 'line',
                smooth: false,
                color: '#00ef00',
                symbol: symbol,
                symbolSize: symbolSize,
                //animation:false,
                markPoint:{
                           //symbol: 'pin',
                            data:[
                                {symbol: 'circle',value:'1',symbolSize:20,xAxis:150,yAxis:700},
                                //{symbol: 'pin',value:'站点1',symbolSize:50,xAxis:100,yAxis:900},
                                //{symbol: 'pin',value:'站点2',symbolSize:50,xAxis:300,yAxis:700},
                               ]
                            },
                data: 'linedata'
            }

    option = {
        title: {
            text: 'Click to Add Points',
            show: false
        },
        tooltip: {
            formatter: function (params) {
                console.log(params);
                if (params.componentType == "markPoint"){
                    var name = params.data.name;
                    var speed = params.data.speed;
                    var x = params.data.xAxis;
                    var y = params.data.yAxis;
                    return ('name:'+name+'</br>'
                    +'speed:'+speed+'</br>'
                    +'xy:'+x.toFixed(2)+','+y.toFixed(2)+'</br>'
                    )
                }
                var data = params.data || [0, 0];
                return data[0].toFixed(2) + ', ' + data[1].toFixed(2);
            }
        },
        grid: {
            left: '0.2%',
            right: '1%',
            top:'1%',
            bottom: '1%',
            containLabel: true
        },
        xAxis: {
            min: 0,
            max: 1000,
            interval: 100,
            type: 'value',
            axisLine: {onZero: false}
        },
        yAxis: {
            min: 0,
            max: 1000,
            interval: 100,
            type: 'value',
            axisLine: {onZero: false}
        },
        series: [
            {
                id: linedata.name[0],
                type: 'line',
                smooth: false,
                color: '#00ef00',
                symbol: symbol,
                symbolSize: symbolSize,
                //animation:false,
                markPoint:{
                           //symbol: 'pin',
                            data:[
                                //{symbol: 'circle',value:'1',symbolSize:20,xAxis:150,yAxis:700},
                                //{symbol: 'pin',value:'站点1',symbolSize:50,xAxis:100,yAxis:900},
                                //{symbol: 'pin',value:'站点2',symbolSize:50,xAxis:300,yAxis:700},
                               ]
                            },
                data: linedata.data[0]
            },
            {
                id: linedata.name[1],
                type: 'line',
                smooth: false,
                color: '#ff0000',
                symbolSize: symbolSize,
                markPoint:{
                            symbol: 'circle',
                            data:[
                                //{symbol: 'circle',value:'2',symbolSize:20,xAxis:700,yAxis:300},
                                //{symbol: 'pin',value:'充电',xAxis:800,yAxis:200},
                                ]
                            },
                data: linedata.data[1]
            }
        ]
    };

    var sock = null;
    var serversocket = "ws://127.0.0.1:8080/markpoint";
    sock = new WebSocket(serversocket);

    var zr = myChart.getZr();

/*
    zr.on('click', function (params) {
        var pointInPixel = [params.offsetX, params.offsetY];
        var pointInGrid = myChart.convertFromPixel('grid', pointInPixel);

        if (myChart.containPixel('grid', pointInPixel)) {
            data.push(pointInGrid);

            myChart.setOption({
                series: [{
                    id: 'a',
                    data: data,
                }]
            });
        }
    });
    zr.on('click', function (params) {
        var pointInPixel = [params.offsetX, params.offsetY];
        var pointInGrid = myChart.convertFromPixel('grid', pointInPixel);

        if (myChart.containPixel('grid', pointInPixel)) {
            //data.push(pointInGrid);
            myChart.setOption({
                series: [{
                    id: linedata.name[1],
                    markPoint:{
                            symbol: 'circle',
                            data:[
                                {symbol: 'circle',value:'2',symbolSize:20,xAxis:700,yAxis:400},
                                {symbol: 'pin',value:'充电',xAxis:800,yAxis:200},
                                ]
                            },
                }]
            });
        }
    });
        */

    zr.on('mousemove', function (params) {
        var pointInPixel = [params.offsetX, params.offsetY];
        zr.setCursorStyle(myChart.containPixel('grid', pointInPixel) ? 'copy' : 'default');
    });

    if (option && typeof option === "object") {
        myChart.setOption(option, true);
    }


    sock.onopen = function(){
        console.log("connect to "+serversocket);
    }
    sock.onclose = function(e){
        console.log("connect closed("+e.code+")");
    }

    sock.onmessage = function(e){
        //console.log("message recevice:"+e.data);
        //var redata = eval(e.data);
        var redata =jQuery.parseJSON(e.data);
        if(redata.line != null){
            var line = redata.line ;
            addpoint(line)
        }else{
            var pointlist = redata.markpoint ;
            change_position(pointlist);
        }
    }

    function send(){
        var smsg = "123456";
        sock.send(smsg);
    }
    
    function addpoint(params){   //line 增加端点

        for(var i=0;i<params.length;i++){
                var name = params[i]['name'];
                var linedata = params[i]['data'];
                var markPoint = params[i]['markPoint'];
                var obj1=Object.assign({},series_template);
                obj1.id = name;
                obj1.data = linedata;
                obj1.markPoint = markPoint;
                newseries.push(obj1);
                /*
                myChart.setOption({
                    series: [{
                        id: name,
                        data: linedata
                    }]
                }); */
        }
         myChart.setOption({
                    series: newseries
                });

        
    }

    function change_position(params){  //改变markpoint 位置
        for(var i=0;i<params.length;i++){
            carname = params[i].name;
            nowdata = newseries[i].markPoint.data;

            if(params[i].position != null){
                nowdata[0].xAxis = params[i]['position'][0];
                nowdata[0].yAxis = params[i]['position'][1];
                //console.log(nowdata);
                myChart.setOption({
                    series: [{
                            id: carname,  //改变对应object的值
                            markPoint:{
                                   data:nowdata
                                    },
                    }]
                });
            }

        }
    }

})
