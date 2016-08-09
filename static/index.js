Date.prototype.withoutTime = function () {
    var d = new Date(this);
    d.setHours(0, 0, 0, 0, 0);
    return d
}
payment.default_on_success = display_result;
var fee_input = $('#fee_input_div input');
var auth_code_input = $('#auth_code_input_div input');
var query_input = $('#query_input');
var result_panel = $('#result_panel');

if (!Cookies.get('device_name'))
{
  $('#device_name_input_div').show();
  var inputs = $('#device_name_input_div input');
  onenter(inputs,function(){
    var val = inputs.val();
    if (!val) return;
    Cookies.set('device_name', val, { expires: 365 });
    $('#device_name_input_div').hide();
  });
}

$('#result_panel [name]').each(function(i,e){
  var e = $(e);
  var name = e.attr('name');
  result_panel[name] = e;
});
onenter(fee_input,function(){auth_code_input.focus();});
onenter(auth_code_input,pay);
onenter(query_input,function(){query(query_input.val());});

function onenter(target,func)
{
  target.on('keypress',function(e){
    if (!e) e = window.event;
    if ((e.keyCode || e.which) == '13'){
      func();
      return false;
    }
  });
}

function msgbox(color,icon,header,content,notify,onApprove,onDeny)
{
  var msg = $('#msg_modal');
  msg.find('.header').removeClass().addClass("ui icon header "+ color).html('<i class="icon '+icon+'"></i>'+ header);
  msg.find('.content').html('<p style="font-size:1.6em">' + content + '</p>');
  if (notify)
  {
    msg.find('.actions').html('<div class="ui ok inverted button">关闭</div>')
    msg.modal().modal('show');
  }
  else
  {
    msg.find('.actions').html('<div class="ui red basic cancel inverted button"><i class="remove icon"></i>取消</div><div class="ui green ok inverted button"><i class="checkmark icon"></i>确认</div>')
    msg.modal({closable : false, onDeny : onDeny, onApprove : onApprove}).modal('show');
  }
}

/* ----- Request ----- */
function pay()
{
  var pay_fee = fee_input.val();
  var auth_code = auth_code_input.val().replace(/[^0-9]/g, '');
  if (!pay_fee)
  {
    fee_input.focus();
    return;
  }
  if (!auth_code)
  {
    auth_code.focus();
    return;
  }
  result_panel.addClass('loading');
  $('#pay_panel').addClass('loading');
  payment.pay(pay_fee,auth_code);
  fee_input.val('');
  auth_code_input.val('');
}
function query(out_trade_no)
{
  out_trade_no = out_trade_no.trim();
  if (out_trade_no.length < 10)
    return;
  result_panel.show();
  result_panel.addClass('loading');
  payment.query(out_trade_no);
}
function get_history_by_day(day)
{
  var to_time = parseInt((new Date()).withoutTime().getTime() / 1000) + 86400;
  if (day > 0)
    var from_time = to_time - 86400 * day;
  else
  {
    var from_time = to_time - 86400 * (-day+1);
    to_time = to_time - 86400 * (-day);
  }
  $('#history_panel').addClass('loading');
  payment.get_history(from_time,to_time,update_history);
}
function get_history_by_date(year,month,day)
{
  var from_time = (new Date(year,month,day)).withoutTime().getTime() / 1000;
  var to_time = from_time + 86400;
  $('#history_panel').addClass('loading');
  payment.get_history(from_time,to_time,update_history);
}

/* ----- Display ----- */
function reset_result()
{
  $('#pay_panel').removeClass('loading');
  result_panel.removeClass('loading');
  result_panel.show();
  $('#result_panel .table [name]').html('').closest('tr').hide();
  result_panel.refresh_btn.off('click').transition('fade in');
  result_panel.display_refund.off('click').transition('fade in');
  result_panel.display_raw.off('click').transition('fade in');
  result_panel.refund_button.off('click');
  result_panel.refund_input.val('');
  result_panel.refund_panel.hide();
  result_panel.raw_data_display.hide();
}
function display_not_empty(td)
{
  if (td.html() != '') td.closest('tr').show();
}
function display_result(data)
{
  console.log('GET',data);
  reset_result();
  query_input.val(data.out_trade_no);
  display_not_empty(result_panel.state.html(format_state(data.state)));
  display_not_empty(result_panel.method.html(format_state(data.method)));
  display_not_empty(result_panel.order_state.html(format_state(data.order_state)));
  display_not_empty(result_panel.create_time.html(format_time(data.create_time)));
  display_not_empty(result_panel.time.html(format_time(data.time)));
  display_not_empty(result_panel.out_trade_no.html(data.out_trade_no));
  display_not_empty(result_panel.total_fee.html(format_money(data.total_fee,'green','',false)));
  display_not_empty(result_panel.refund_fee.html(format_money(data.refund_fee,'orange')));
  display_not_empty(result_panel.orginal_fee.html(format_money(data.orginal_fee,'','',false)));
  display_not_empty(result_panel.pay_device_name.html(data.pay_device_name));
  display_not_empty(result_panel.refund_device_name.html(data.refund_device_name));
  result_panel.refresh_btn.on('click',function(){query(data.out_trade_no);});
  result_panel.display_refund.on('click',function(){
    result_panel.refund_panel.show();
    $(this).transition('fade out');
  });
  result_panel.display_raw.on('click',function(){
    result_panel.raw_data_display.show();
    $(this).transition('fade out');
  });
  if (data.order_state=='success')
    result_panel.refund_button.transition('fade in');
  else
    result_panel.refund_button.transition('fade in');
  result_panel.refund_button.on('click',function(){
    var fee = result_panel.refund_input.val();
    if (fee)
    {
      result_panel.addClass('loading');
      payment.refund(data.out_trade_no,fee,data.orginal_fee || data.total_fee);
    }
  });
  result_panel.raw_data_display.html(JSON.stringify(data.raw, null, 2).replace(/\n/g,'<br>'));
}
function update_history(data)
{
  $('#history_panel').removeClass('loading');
  console.log(data);
  var tbody = $('#history_table tbody').empty();
  var sums = {am:[0,0],mo:[0,0],pm:[0,0],ev:[0,0],su:[0,0]};
  $.each(data,function(i,e){
    var t = $('<tr></tr>');
    t.append('<td>'+(i+1)+'</td><td>'+format_time(e.create_time)+'</td>');
    t.append($('<td></td>').append(format_trade_no(e.out_trade_no)));
    t.append('<td>'+format_state(e.method)+'</td><td>'+format_state(e.order_state)+'</td><td>'+format_money(e.total_fee)+'</td>');
    tbody.prepend(t);
  });
  if (tbody.children().length == 0)
    tbody.prepend('无数据');
}

/* ----- Formating ----- */
function format_time(timestamp)
{
  if (!timestamp) return;
  var date = new Date(timestamp * 1000);
  return date.toLocaleString();
}
function format_money(fee,color,size,check)
{
  color = color || '';
  size = size || '';
  if (check == undefined)  check = true;
  if (fee)
    if ((check && parseFloat(fee)>0) || !check)
      return '<div class="ui '+size+' '+color+' basic label" style="margin:0;"><i class="icon yen"></i>'+fee+'</div>';
  return '';
}
function format_trade_no(out_trade_no)
{
  var l = $('<div style="cursor:pointer;">'+out_trade_no+'</div>');
  l.on('click',function(){query(out_trade_no);});
  return l;
}
function format_state(state)
{
  if (state == 'success')
    return '<div class="ui green label"><i class="icon checkmark"></i>成功</div>';
  if (state == 'paying')
    return '<div class="ui orange label"><i class="icon wait"></i>支付中</div>';
  if (state == 'fail')
    return '<div class="ui red label"><i class="icon warning sign"></i>失败</div>';
  if (state == 'closed')
    return '<div class="ui orange label"><i class="icon minus circle"></i>交易关闭</div>';
  if (state == 'refund')
    return '<div class="ui yellow label"><i class="icon reply"></i>发生退款</div>';
  if (state == 'alipay')
    return '<div class="ui blue label">支付宝</div>';
  if (state == 'micropay')
    return '<div class="ui olive label">微信</div>';
  return '';
}

/* ----- Webcam -----*/
function scanner_open()
{
  $('#interactive').show();
  $('#webcam [name=open]').hide();
  $('#webcam [name=close]').show();
  scan_barcode(function(code){
    auth_code_input.val(code);
    pay(); // Try to pay
    scanner_close();
  },1,$(window).width()-50,function(){
    scanner_close()
    $('#webcam').addClass('disabled').text('你的设备不支持摄像头调用');
  });
}
function scanner_close()
{
  $('#interactive').hide().empty();
  $('#webcam [name=open]').show();
  $('#webcam [name=close]').hide();
}
/* ----- URLParamter -----*/
$(function(){
  var query = get_url_parameter('query');
  if (query)
  {
    var y = query.slice(0,4);
    var m = query.slice(4,6) - 1;
    var d = query.slice(6,8);
    get_history_by_date(y,m,d);
  }
  $('#interactive').hide();
});
