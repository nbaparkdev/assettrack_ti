package utils

import "time"

// NowSP returns current time in America/Sao_Paulo as naive (no timezone info)
// Mirrors Python's now_sp() from app/core/datetime_utils.py
func NowSP() time.Time {
	loc, err := time.LoadLocation("America/Sao_Paulo")
	if err != nil {
		return time.Now()
	}
	return time.Now().In(loc)
}

// StringPtr returns a pointer to a string
func StringPtr(s string) *string { return &s }

// UintPtr returns a pointer to a uint
func UintPtr(u uint) *uint { return &u }

// BoolPtr returns a pointer to a bool
func BoolPtr(b bool) *bool { return &b }
