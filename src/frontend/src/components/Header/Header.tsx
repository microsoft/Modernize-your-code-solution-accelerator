import React, { useEffect, useRef, useState } from "react";
import { Subtitle2 } from "@fluentui/react-components";
import {getUserInfo}  from "../../api/auth";
import ContosoLogo from "../../assets/Contoso.png";

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
  logo?: React.ReactNode;
  title?: string;
  subtitle?: string;
  children?: React.ReactNode;
};




const Header: React.FC<HeaderProps> = ({ logo, title = "Contoso", subtitle, children }) => {
  const [showAuthMessage, setShowAuthMessage] = useState<boolean | undefined>();
  const firstRender = useRef(true);
  useEffect(() => {
    console.log("calling list ");
    getUserInfoList();
  }, []);

  const getUserInfoList = async () => {
  const userInfoList = await getUserInfo();
  if (
    (!userInfoList || userInfoList.length === 0) &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1"
  ) {
    setShowAuthMessage(true);
  } else {
    setShowAuthMessage(false);
  }
  };


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
        zIndex:1000,
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
        <img src={ContosoLogo} alt="Contoso" style={{ width: "25px", height: "25px" }} />

        {/* Render title and optional subtitle */}
        <Subtitle2 style={{ whiteSpace: "nowrap", marginTop: "-2px" }}>
          {title}
          {subtitle && (
            <span style={{ fontWeight: "400" }}> | {subtitle}</span>
          )}
        </Subtitle2>
      </div>

      {/* HEADER TOOLBAR (rendered only if passed as a child) */}
      {children}
    </header>
  );
};

export default Header;
