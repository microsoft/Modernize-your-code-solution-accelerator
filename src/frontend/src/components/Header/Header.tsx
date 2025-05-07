import React from "react";
import { Subtitle2 } from "@fluentui/react-components";
import "./Header.scss"; // Import for styling
import { useNavigate } from "react-router-dom";
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

const Header: React.FC<HeaderProps> = ({ title = "Contoso", subtitle, children }) => {
  const navigate = useNavigate();
  return (
    <header
      className="header"
      data-figma-component="Header"
    >
      <div
        className="headerContainer"
        onClick={() => {
          navigate("/"); // Redirect to home page on logo click
        }
      }
      >
        {/* Render custom logo or default MsftColor logo */}
        {/* <Avatar shape="square" color={null} icon={logo || <MsftColor />} /> */}
        <img src="/images/Contoso.png" alt="Contoso" className="headerImage"/>

        {/* Render title and optional subtitle */}
        <Subtitle2 className="subTitle">
          {title}
          {subtitle && (
            <span className="fw_400"> | {subtitle}</span>
          )}
        </Subtitle2>
      </div>

      {/* HEADER TOOLBAR (rendered only if passed as a child) */}
      {children}
    </header>
  );
};

export default Header;
