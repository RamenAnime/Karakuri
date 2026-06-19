// Cliff sensor bracket. This is the part that keeps the robot off
// your stairs. Holds a VL53L0X time of flight breakout (or a Sharp
// GP2Y0A41 IR sensor on the wide slots) pointing straight down past
// the deck edge. Mount one at each front corner and one each side of
// the rear so the robot is protected driving forward and reversing.
// Print 4. Flat side down, no supports.

include <common.scad>

drop = 28;          // sensor face below deck level, keeps floor in range
tab_w = 30;

module cliff_bracket() {
    difference() {
        union() {
            // Deck tab
            rounded_plate(tab_w, 34, 5, 3);
            // Drop leg
            translate([0, -17 + 2.5, 0])
                rotate([90, 0, 0])
                    linear_extrude(5)
                        translate([0, -drop / 2]) square([tab_w, drop], center = true);
            // Sensor shelf at the bottom of the leg
            translate([0, -17 - 14, -drop])
                linear_extrude(5) square([tab_w, 28], center = true);
        }
        // Deck holes
        translate([0, 10, 0]) hole(m3, 5);
        translate([0, -2, 0]) hole(m3, 5);
        // Sensor window and slots in the shelf
        translate([0, -17 - 14, -drop]) {
            hole(12, 5);
            for (x = [-10, 10]) translate([x, 0, 0]) slot(2.4, 6, 5);
        }
    }
}

cliff_bracket();
