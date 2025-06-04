import React, { useState, useEffect, ReactNode, ReactElement } from "react";
import PanelToolbar from "./PanelLeftToolbar.js"; // Import to identify toolbar
import "./Panels.scss"; // Import for styling

interface PanelLeftProps {
  panelWidth?: number;
  panelResize?: boolean;
  children?: ReactNode;
}

const PanelLeft: React.FC<PanelLeftProps> = ({
  panelWidth = 500,
  panelResize = true,
  children,
}) => {
  const [width, setWidth] = useState(panelWidth);
  const [isHandleHovered, setIsHandleHovered] = useState(false);

  useEffect(() => {
    setWidth(panelWidth);
  }, [panelWidth]);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!panelResize) return;

    const startX = e.clientX;
    const startWidth = width;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(
        500,
        Math.max(256, startWidth + (moveEvent.clientX - startX))
      );
      setWidth(newWidth);
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);

      // Re-enable text selection
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);

    // Disable text selection
    document.body.style.userSelect = "none";
  };

  const childrenArray = React.Children.toArray(children) as ReactElement[];
  const toolbar = childrenArray.find(
    (child) => React.isValidElement(child) && child.type === PanelToolbar
  );
  const content = childrenArray.filter(
    (child) => !(React.isValidElement(child) && child.type === PanelToolbar)
  );

  return (
    <div
      className="panelLeft"
      style={{
        width: `${width}px`,
        borderRight: panelResize
          ? isHandleHovered
            ? "2px solid var(--colorNeutralStroke2)"
            : "2px solid transparent"
          : "none",
      }}
    >
      {toolbar && <div className="fs_0">{toolbar}</div>}

      <div
        className="panelContent"
      >
        {content}
      </div>

      {panelResize && (
        <div
          className="resizeHandle"
          onMouseDown={handleMouseDown}
          onMouseEnter={() => setIsHandleHovered(true)}
          onMouseLeave={() => setIsHandleHovered(false)}
          style={{
            backgroundColor: isHandleHovered
            ? "var(--colorNeutralStroke2)"
            : "transparent",
          }}
        />
      )}
    </div>
  );
};

export default PanelLeft;
