// Backpack mount for a late 2014 Mac mini (Macmini7,1, 197 x 197 x 36).
// The mini is wider than the chest bay, so it rides outside the rear as
// a backpack: two U channel rails bolt across the chest rear corner
// posts, hold the mini's top and bottom edges, and stand it 14 mm off
// the rear panel so the exhaust fan blows into an open chimney gap
// behind the chest. Two retaining clips pinch the mini at the rail
// ends. Print 2 rails and 2 clips; one rail plus one clip per plate.
// Flat, no supports.
include <common.scad>

rail_len = 214;
ch_w = 37.5;      // channel width, mini 36 plus pad
wall = 6;
standoff = 14;    // chimney gap depth
lip_h = 14;

module mini_rail() {
    difference() {
        // base + two channel walls
        union() {
            cube([rail_len, ch_w + 2 * wall, standoff], center = false);
            cube([rail_len, wall, standoff + lip_h]);
            translate([0, ch_w + wall, 0]) cube([rail_len, wall, standoff + lip_h]);
        }
        // M4 to the chest rear corner posts, 164 apart, plus centre M3 to the ring edge
        for (x = [rail_len / 2 - 82, rail_len / 2 + 82])
            translate([x, (ch_w + 2 * wall) / 2, 0]) hole(m4, standoff);
        translate([rail_len / 2, (ch_w + 2 * wall) / 2, 0]) hole(m3, standoff);
        // clip screw holes in the wall ends
        for (x = [10, rail_len - 10])
            translate([x, wall / 2, standoff + lip_h / 2])
                rotate([90, 0, 0]) translate([0, 0, -wall - 1]) cylinder(d = m3, h = 2 * wall + ch_w + 2);
        // chimney vent slots through the base
        for (x = [30, 70, 110, 150])
            translate([x + 12, (ch_w + 2 * wall) / 2, 0]) slot(8, 20, standoff);
    }
}
module mini_clip() {
    difference() {
        union() { cube([8, 50, 6]); cube([8, 6, 20]); }
        translate([4, 25, 0]) slot(m3, 14, 6);
    }
}
mini_rail();
translate([0, 70, 0]) mini_clip();
