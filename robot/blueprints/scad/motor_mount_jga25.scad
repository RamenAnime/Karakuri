// Saddle clamp mount for a JGA25-370 (25 mm body) gear motor.
// Universal clamp style so the exact face hole pattern of your motor
// batch does not matter. Print 2. Orientation: as modelled, flat base
// down, no supports.

include <common.scad>

motor_d = 25.4;       // motor body plus clearance
saddle_len = 32;      // length of body gripped
base_t = 5;
wall = 6;
drop = 22;            // axle centre height below deck underside

module motor_mount() {
    difference() {
        union() {
            // Base plate that bolts to the deck slots
            translate([0, 0, 0]) rounded_plate(50, saddle_len + 14, base_t, 4);
            // Saddle block
            translate([0, 0, base_t])
                linear_extrude(drop + motor_d / 2)
                    square([motor_d + 2 * wall, saddle_len], center = true);
        }
        // Motor bore
        translate([0, -saddle_len / 2 - 1, base_t + drop + motor_d / 2])
            rotate([-90, 0, 0])
                cylinder(d = motor_d, h = saddle_len + 2);
        // Open the top for the clamp strap
        translate([0, 0, base_t + drop + motor_d / 2])
            linear_extrude(motor_d)
                square([motor_d - 6, saddle_len + 2], center = true);
        // Clamp bolt holes through the side walls
        for (y = [-9, 9])
            translate([0, y, base_t + drop + motor_d / 2 + 4])
                rotate([0, 90, 0]) translate([0, 0, -(motor_d / 2 + wall + 1)])
                    cylinder(d = m3, h = motor_d + 2 * wall + 2);
        // Deck bolt holes
        four_holes(40, saddle_len + 4, m3, base_t);
    }
}

module clamp_strap() {
    difference() {
        rounded_plate(motor_d + 2 * wall, 24, 5, 3);
        for (y = [-9, 9]) translate([0, y, 0]) hole(m3, 5);
        translate([0, 0, 2]) rounded_plate(motor_d - 6, 26, 4, 1);
    }
}

motor_mount();
translate([60, 0, 0]) clamp_strap();
