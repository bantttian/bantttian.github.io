<?php
class A extends B implements D, E {
    use T, S;
    const X = 'Y', Y = 'X';
    public $foo, $bar;
    abstract function test();
}
