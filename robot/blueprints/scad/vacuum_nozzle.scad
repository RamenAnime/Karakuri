// HANE floor nozzle. Wide rectangular mouth at the floor narrowing to
// a 35 mm round port that couples to the donor vacuum hose through the
// hose coupler part. Bolts under the deck intake with 4 x M3. The
// mouth sits 3 mm off the floor at default ride height. Print port
// end up with supports enabled, or split at your slicer's discretion.

include <common.scad>

mouth_w = 120;
mouth_d = 16;
port_d = 35;
neck_h = 55;
wall_t = 2.5;

module outer() {
    hull() {
        linear_extrude(2)
            offset(r = 4) offset(delta = -4)
                square([mouth_w, mouth_d], center = true);
        translate([0, 0, neck_h]) cylinder(d = port_d, h = 2);
    }
    translate([0, 0, neck_h]) cylinder(d = port_d, h = 22);
}

module inner() {
    hull() {
        translate([0, 0, -1])
            linear_extrude(2)
                offset(r = 3) offset(delta = -3)
                    square([mouth_w - 2 * wall_t, mouth_d - 2 * wall_t], center = true);
        translate([0, 0, neck_h]) cylinder(d = port_d - 2 * wall_t, h = 2);
    }
    translate([0, 0, neck_h]) cylinder(d = port_d - 2 * wall_t, h = 25);
}

module vacuum_nozzle() {
    difference() {
        union() {
            outer();
            // Mounting flange partway up the neck, lands on deck underside
            translate([0, 0, neck_h - 14])
                rounded_plate(70, 70, 5, 6);
        }
        inner();
        translate([0, 0, neck_h - 14]) four_holes(56, 56, m3, 5);
    }
}

vacuum_nozzle();
