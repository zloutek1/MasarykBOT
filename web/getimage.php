<?php
$rootDIR = "/mnt/D/dockerProjects/MasarykBOT/";
if (isset($_GET["src"])) {
    $ls = scandir($rootDIR."bot/assets/");

    if (in_array($_GET["src"], $ls)) {
        header('Content-type: image/png;');
        $p = $rootDIR."bot/assets/".$_GET["src"];
        $a = file_get_contents($p);
        echo $a;
    }
}
?>
