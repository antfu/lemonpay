var payment = {};
payment.submit = function(method,type,data,onSuccess,onFail)
{
  data.method = method;
  $.ajax({
    method: 'post',
    url: "/api/payment/" + type,
    data: JSON.stringify(data),
    dataType: 'json',
    success: function(data, textStatus, jqXHR)
    {
      if (!onSuccess)
        onSuccess = payment.default_on_success;
      onSuccess(JSON.parse(jqXHR.responseText));
    },
    error: function(jqXHR, textStatus, errorThrown)
    {
      console.log('ERROR', jqXHR.status, jqXHR.statusText)
      if (!onFail)
        onFail = payment.default_on_fail;
      onFail(errorThrown);
    }
  })
}

payment.detecting_method_by_auth_code = function(auth_code)
{
  if (auth_code.startsWith('11')
  || auth_code.startsWith('12')
  || auth_code.startsWith('13')
  || auth_code.startsWith('14')
  || auth_code.startsWith('15'))
    return 'mircopay';
  else
    return 'alipay';
}

payment.detecting_method_by_trade_no = function(out_trade_no)
{
  if (out_trade_no.startsWith('zfb')) return 'alipay';
  if (out_trade_no.startsWith('wx'))  return 'mircopay';
  return 'alipay';
}

payment.generate_trado_no = function(method)
{
  var prefix = '';
  if (method == 'alipay')   prefix = 'zfb';
  if (method == 'mircopay') prefix = 'wx';
  return prefix + (new Date()).toISOString().replace(/[-TZ.:]/g,'');
}

payment.pay = function(fee_in_yuan,auth_code,onSuccess,onFail)
{
  var method = payment.detecting_method_by_auth_code(auth_code);
  var out_trade_no = payment.generate_trado_no(method);
  var obj = {fee_in_yuan:fee_in_yuan,auth_code:auth_code,out_trade_no:out_trade_no}
  payment.submit(method,'pay',obj,onSuccess,onFail)
}

payment.query = function(out_trade_no,onSuccess,onFail)
{
  var method = payment.detecting_method_by_trade_no(out_trade_no);
  var obj = {out_trade_no:out_trade_no};
  payment.submit(method,'query',obj,onSuccess,onFail)
}

payment.refund = function(out_trade_no,refund_fee_in_yuan,total_fee_in_yuan,onSuccess,onFail)
{
  var method = payment.detecting_method_by_trade_no(out_trade_no);
  var obj = {out_trade_no:out_trade_no,refund_fee_in_yuan:refund_fee_in_yuan,total_fee_in_yuan:total_fee_in_yuan};
  payment.submit(method,'refund',obj,onSuccess,onFail)
}

payment.default_on_success = function(data)
{
  console.log(data);
}
payment.default_on_fail = function(error)
{
  alert(error);
}

payment.get_history = function(from_time,to_time,onSuccess,onFail)
{
  $.ajax({
    method: 'post',
    url: "/api/history",
    data: JSON.stringify({from_time:from_time,to_time:to_time}),
    dataType: 'json',
    success: function(data, textStatus, jqXHR)
    {
      if (onSuccess)
        onSuccess(JSON.parse(jqXHR.responseText));
    },
    error: function(jqXHR, textStatus, errorThrown)
    {
      console.log('ERROR', jqXHR.status, jqXHR.statusText)
      if (onFail)
        onFail(errorThrown);
    }
  })
}

/*=== Url parameter ===*/
function get_url_parameter(sParam) {
  var sPageURL = decodeURIComponent(window.location.search.substring(1)),
      sURLVariables = sPageURL.split('&'),
      sParameterName,
      i;
  for (i = 0; i < sURLVariables.length; i++) {
    sParameterName = sURLVariables[i].split('=');
    if (sParameterName[0] === sParam) {
        return sParameterName[1] === undefined ? true : sParameterName[1];
    }
  }
}
