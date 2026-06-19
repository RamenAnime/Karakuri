// E-stop holder for a standard 22 mm mushroom emergency stop button,
// mounted at the rear of the deck where you can reach it from above.
// This is the physical layer of the KODAMA kill switch: the button
// breaks motor and vacuum power directly, no software in the loop.
// Print flat side down, no supports.

include <common.scad>

module estop_mount() {
    difference() {
        union() {
            rounded_plate(40, 56, 5, 5);
            translate([0, 8, 0]) cylinder(d = 40, h = 26);
        }
        // 22 mm panel hole
        translate([0, 8, 0]) hole(22.5, 26);
        // Anti-rotation notch
        translate([0, 8 + 12.2, 18]) linear_extrude(9) square([4.2, 4], center = true);
        // Deck bolts
        translate([0, -20, 0]) hole(m4, 5);
        translate([0, -6, 0]) hole(m4, 5);
    }
}

estop_mount();
