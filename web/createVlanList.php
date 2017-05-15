<?php

define("SWITCH_USERNAME", "SWITCH_USERNAME");
define("SWITCH_PASSWORD", "SWITCH_PASSWORD");
define("ROUTER_NAME", "ROUTER_NAME");
define("SWITCH_NAME", "SWITCH_NAME");

if(is_file("src/networkOverview.json"))
    $networkOverview = file_get_contents("src/networkOverview.json");
else{
    // This is not recommended as it might place a heay load on the switches. Try and use the local file above if possible
    $local = false;
    $networkOverview = shell_exec("python ../network_overview.py " . SWITCH_USERNAME . " " . SWITCH_PASSWORD . " " . ROUTER_NAME . " " . SWITCH_NAME );
}

$ports = json_decode($networkOverview)->ports;
?>

<html><head>
    <script
        src="https://code.jquery.com/jquery-1.12.4.js"
        integrity="sha256-Qw82+bXyGq6MydymqBxNPYTaUXXq7c8v3CwiYwLLNXU="
        crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.15/js/jquery.dataTables.min.js"></script><script>
        $(document).ready(function(){
            ResultTable = $('table').DataTable( {
                order: [0, 'asc'],
                lengthMenu: [100, 1000, 10000]
            } );
        });
    </script>
    <title>VLAN Page</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" crossorigin="anonymous">
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.15/css/jquery.dataTables.min.css">
</head>
<body>
<?php if(!$local) echo "WARNING: no local file found, used direct polling of the switches";?>
<form action="ip_lookup.php" method="post">
    <label for="ip_lookup">Lookup IP-Address or Hostname: </label><input id="ip_lookup" type="text" name="ip_lookup">
    <input type="submit">
</form>
<br>
<br />
<table class="tablesorter">
    <thead><tr>
        <th>patchid</th>
        <th>vlanid</th>
        <th>vlanName</th>
        <th>hostname</th>
        <th>interface</th>
    </tr></thead>
<?php
foreach($ports as $port){
    if(isset($port->vlanconfig)) {
        if ($port->vlanconfig == "dynamic") {
            $vlanName = "Dynamic";
        } else {
            $vlanName = $port->vlanname;
        }
    }
    else
        $vlanName = $port->vlanname;

    $body .= "<tr><td>".$port->patchid."</td><td>".$port->vlanid."</td><td>" . $vlanName ."</td><td>".$port->hostname."</td><td>".$port->interface."</td></tr>";
}

$body .= "</table>";
echo $body;
?>