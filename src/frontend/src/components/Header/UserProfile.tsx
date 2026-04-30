import React from "react";
import {
  Avatar,
  Button,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  MenuDivider,
  Tooltip,
} from "@fluentui/react-components";
import {
  Person20Regular,
  SignOut20Regular,
} from "@fluentui/react-icons";
import useAuth from "../../msal-auth/useAuth";

/**
 * @component UserProfile
 * @description Renders an avatar in the header. Clicking opens a menu showing
 *   the signed-in user's name and email along with a Logout option.
 *   Designed to be rendered only when MSAL authentication is enabled.
 */
const getInitials = (name?: string, username?: string): string => {
  const source = name && name.trim().length > 0 ? name : username || "";
  if (!source) return "U";

  if (source.includes("@")) {
    const prefix = source.split("@")[0];
    const parts = prefix.split(/[._-]/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return prefix.substring(0, 2).toUpperCase();
  }

  return source
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
};

const UserProfile: React.FC = () => {
  const { isAuthenticated, accounts, logout } = useAuth();

  if (!isAuthenticated || !accounts || accounts.length === 0) {
    return null;
  }

  const account = accounts[0];
  const name = account?.name || account?.username || "User";
  const email = account?.username || "";
  const initials = getInitials(account?.name, account?.username);

  const handleLogout = (e: React.MouseEvent) => {
    e.stopPropagation();
    logout();
  };

  return (
    <Menu positioning="below-end">
      <MenuTrigger disableButtonEnhancement>
        <Tooltip content={email || name} relationship="label">
          <Button
            appearance="subtle"
            shape="circular"
            aria-label={`Signed in as ${name}`}
            style={{ padding: 0, minWidth: "auto" }}
            onClick={(e) => e.stopPropagation()}
          >
            <Avatar
              name={name}
              initials={initials}
              color="colorful"
              size={32}
            />
          </Button>
        </Tooltip>
      </MenuTrigger>
      <MenuPopover>
        <MenuList>
          <MenuItem
            icon={<Person20Regular />}
            disabled
            style={{ cursor: "default", opacity: 1 }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                minWidth: 0,
                maxWidth: 240,
              }}
            >
              <span
                style={{
                  fontWeight: 600,
                  fontSize: 14,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  color: "var(--colorNeutralForeground1)",
                }}
              >
                {name}
              </span>
              {email && (
                <span
                  style={{
                    fontSize: 12,
                    color: "var(--colorNeutralForeground3)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {email}
                </span>
              )}
            </div>
          </MenuItem>
          <MenuDivider />
          <MenuItem icon={<SignOut20Regular />} onClick={handleLogout}>
            Logout
          </MenuItem>
        </MenuList>
      </MenuPopover>
    </Menu>
  );
};

export default UserProfile;
