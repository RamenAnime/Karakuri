// Electronics tray. Raspberry Pi 5 pattern (58 x 49, M2.5) plus an
// M3 grid for the motor driver, buck converters, and the Kinect's 12 V
// adapter board. Stands on 4 x M3 deck standoffs. Print flat.

include <common.scad>

module electronics_tray() {
    difference() {
        rounded_plate(130, 95, 4, 6);
        // Deck standoffs
        four_holes(110, 40, m3, 4);
        // Raspberry Pi 5
        translate([-28, 14, 0]) four_holes(58, 49, m2_5, 4);
        // General M3 grid for driver and bucks
        for (x = [20, 40, 56], y = [-32, -12, 8, 28])
            translate([x, y, 0]) hole(m3, 4);
        // Zip tie slots
        for (x = [-55, 0, 55])
            translate([x, -40, 0]) slot(3.2, 8, 4);
    }
}

electronics_tray();
