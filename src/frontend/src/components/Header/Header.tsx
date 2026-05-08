import React from "react";
import { Subtitle2 } from "@fluentui/react-components";
import UserProfile from "./UserProfile";

/**
 * @component
 * @name Header
 * @description A header component for displaying a logo, title, and optional subtitle.
 * 
 * @prop {React.ReactNode} [logo] - Custom logo (defaults to Microsoft icon).
 * @prop {string} [title="Microsoft"] - Main title text.
 * @prop {string} [subtitle] - Optional subtitle displayed next to the title.
 * @prop {React.ReactNode} [children] - Optional header toolbar (e.g., buttons, menus).
 */
type HeaderProps = {
  title?: string;
  subtitle?: string;
  children?: React.ReactNode;
};

// Determine once whether MSAL authentication is enabled, so the hooks inside
// UserProfile (which require MsalProvider in the tree) are only mounted when safe.
// window.appConfig is set in main.jsx after fetching /config; falls back to
// false when the config has not loaded or auth is disabled.
const isAuthEnabled = (): boolean => {
  if (typeof window === "undefined") return false;
  return Boolean(window.appConfig && window.appConfig.ENABLE_AUTH);
};

const Header: React.FC<HeaderProps> = ({ title = "Contoso", subtitle, children }) => {
  const authEnabled = isAuthEnabled();
  const hasToolbarContent = React.Children.count(children) > 0 || authEnabled;

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        width: "100%",
        backgroundColor: "#fafafa",
        borderBottom: "1px solid var(--colorNeutralStroke2)",
        padding: "16px",
        height: "64px",
        boxSizing: "border-box",
        gap: "12px",
        position: 'fixed',
        zIndex: 1000,
      }}
      data-figma-component="Header"
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "8px",
        }}
      >
        {/* Render custom logo or default MsftColor logo */}
        {/* <Avatar shape="square" color={null} icon={logo || <MsftColor />} /> */}
        <img src="/images/Contoso.png" alt="Contoso" style={{ width: "25px", height: "25px" }} />

        {/* Render title and optional subtitle */}
        <Subtitle2 style={{ whiteSpace: "nowrap", marginTop: "-2px" }}>
          {title}
          {subtitle && (
            <span style={{ fontWeight: "400" }}> | {subtitle}</span>
          )}
        </Subtitle2>
      </div>

      {/* HEADER TOOLBAR (rendered only when there is toolbar content
          or the auth-enabled user profile menu to display) */}
      {hasToolbarContent && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          {children}
          {authEnabled && <UserProfile />}
        </div>
      )}
    </header>
  );
};

export default Header;
