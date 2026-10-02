// Roles allowed into the school-management screens; the API (IsStaffRole) still also accepts STAFF.
export const MANAGEMENT_ROLES = ['ADMIN']

const HOME_PATHS = {
	STUDENT: '/student/home',
	TEACHER: '/teacher/home',
	PARENT: '/parent/home',
	OBSERVER: '/observer/home',
	STAFF: '/staff/home',
}

// A session with no stored role keeps the management UI; the server still decides what it may call.
export const isManagementUser = (user) => !user?.role || MANAGEMENT_ROLES.includes(user.role)

export const homePathFor = (user) => (isManagementUser(user) ? '/admin/home' : HOME_PATHS[user?.role] || '/me')
