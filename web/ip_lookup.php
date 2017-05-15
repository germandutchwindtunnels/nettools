<?php

define("SWITCH_USERNAME", "SWITCH_USERNAME");
define("SWITCH_PASSWORD", "SWITCH_PASSWORD");
define("ROUTER_NAME", "ROUTER_NAME");
define("SWITCH_NAME", "SWITCH_NAME");

if(!isset($_POST['ip_lookup']) || $_POST['ip_lookup'] == "")
    exit("No data sent");

if(inet_pton($ip) === false) { //Not an IP-adres, try for hostname
    $ip = gethostbyname($ip);
    if(inet_pton($ip) === false)
        exit("Not a valid IP-address, and hostname not found");
}

if(is_file("src/networkOverview.json"))
    $networkOverview = file_get_contents("src/networkOverview.json");
else{
    // This is not recommended as it might place a heay load on the switches. Try and use the local file above if possible
    $local = false;
    $networkOverview = shell_exec("python ../network_overview.py " . SWITCH_USERNAME . " " . SWITCH_PASSWORD . " " . ROUTER_NAME . " " . SWITCH_NAME );
}

$networkOverview = json_decode($networkOverview);

$arp = $networkOverview->arp;
$mac = $networkOverview->mac;
$allPorts = $networkOverview->ports;

$ip_mac = "0000.0000.0000";
foreach($arp as $arp_entry) {
    $arp_entry_ip = $arp_entry->ip;
    $arp_entry_mac = $arp_entry->macaddress;
    if($arp_entry_ip == $ip)
        $ip_mac = $arp_entry_mac;
}

$results = [];
foreach($mac as $mac_entry) {
    if ($mac_entry->macaddress == $ip_mac) {
        $results[]=$mac_entry;
    }
}

uasort($results, "uncertainty_sort");

function uncertainty_sort($a, $b){
    if($a->uncertainty == $b->uncertainty){
        return 0;
    }
    return ($a->uncertainty < $b->uncertainty) ? -1 : 1;
}

?>

    <html><head>
    <script
        src="https://code.jquery.com/jquery-1.12.4.js"
        integrity="sha256-Qw82+bXyGq6MydymqBxNPYTaUXXq7c8v3CwiYwLLNXU="
        crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.15/js/jquery.dataTables.min.js"></script>
    <script>
    $(document).ready(function(){
        ResultTable = $('table').DataTable( {
            order: [1, 'asc'],
            } );
        });
    </script>
    <title>IP lookup</title>
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
            <th>macaddress</th>
            <th>uncertainty</th>
            <th>patchid</th>
            <th>hostname</th>
            <th>vlanid</th>
            <th>vlanname</th>
            <th>port</th>
        </tr></thead>
<?php
foreach($results as $result){
    $body .= "<tr><td>".$result->macaddress."</td><td>".$result->uncertainty."</td><td>".$result->patchid."</td><td>".$result->hostname."</td><td>".$result->vlanid."</td><td>".$result->vlanname."</td><td>".$result->port."</td></tr>";
}

$body .= "</table>";
echo $body;
?>