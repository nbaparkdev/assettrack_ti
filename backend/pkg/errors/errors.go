package errors

import "net/http"

// AppError represents a structured API error
type AppError struct {
	StatusCode int    `json:"-"`
	Detail     string `json:"detail"`
}

func (e *AppError) Error() string { return e.Detail }

func NewBadRequest(detail string) *AppError {
	return &AppError{StatusCode: http.StatusBadRequest, Detail: detail}
}

func NewUnauthorized(detail string) *AppError {
	return &AppError{StatusCode: http.StatusUnauthorized, Detail: detail}
}

func NewForbidden(detail string) *AppError {
	return &AppError{StatusCode: http.StatusForbidden, Detail: detail}
}

func NewNotFound(detail string) *AppError {
	return &AppError{StatusCode: http.StatusNotFound, Detail: detail}
}

func NewConflict(detail string) *AppError {
	return &AppError{StatusCode: http.StatusConflict, Detail: detail}
}

func NewInternal(detail string) *AppError {
	return &AppError{StatusCode: http.StatusInternalServerError, Detail: detail}
}
