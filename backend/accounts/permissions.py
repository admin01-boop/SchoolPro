from rest_framework.permissions import BasePermission

# Only ADMIN/STAFF may use the management API today. Extend with explicit
# per-role classes (IsTeacher, IsParent, IsStudent) once those portals exist,
# rather than widening this check.
STAFF_ROLES = {'ADMIN', 'STAFF'}


class IsStaffRole(BasePermission):
    """Authenticated users with an ADMIN/STAFF role (or Django superusers)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.must_change_password:
            return False
        return user.is_superuser or user.role in STAFF_ROLES


def role_required(*roles):
    """Permission class allowing only authenticated users whose role is one of `roles`."""
    allowed = set(roles)

    class RoleRequired(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            return bool(
                user and user.is_authenticated and not user.must_change_password and user.role in allowed
            )

    RoleRequired.__name__ = 'IsRole_' + '_'.join(sorted(allowed))
    return RoleRequired


IsTeacher = role_required('TEACHER')
IsParent = role_required('PARENT')
IsStudent = role_required('STUDENT')
