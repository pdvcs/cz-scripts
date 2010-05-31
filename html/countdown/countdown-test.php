<?php
  // tested on PHP 5.3.2
 
  function get_singular_or_plural($q, $singular_form) {
    if ($q == 1) {
      return $q . ' ' . $singular_form;
    } else {
      return $q . ' ' . $singular_form . 's';
    }
  }
 
  date_default_timezone_set('Europe/London');
  $now = date_create('now');
  $target = date_create('2010-06-18 19:00:00');
  $dl = explode(' ', $target->diff($now)->format('%m %d %h %i %a'));
 
  $output = get_singular_or_plural($dl[0], 'month') . ' '
    . get_singular_or_plural($dl[1], 'day') . ' '
    . get_singular_or_plural($dl[2], 'hour') . ' '
    . get_singular_or_plural($dl[3], 'minute') . ' '
    . '('
    . get_singular_or_plural($dl[4], 'day')
    . ' total)';
   
  echo $output;
?>
